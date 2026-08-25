import copy
import logging
import os
import time

from src.agent_actions.status_reporter import StatusReporter
from src.constants import FLOW_VERSION
from src.models.settings import Settings
from src.providers.path_provider import PathProvider
from src.runners.workflow_methods import FlowMethodMap
from src.agents.agent_builder import AgentBuilder
from src.utils import storage_provider
from src.utils import dir_utils
from src.utils.storage_provider import read_from_json_file, file_exists

# STEP TIME ESTIMATES
# Rough estimates for progress tracking and ETA calculations
LLM_STEP_TIME = 40   # 40s → LLM calls (slow, network & compute bound)
IO_STEP_TIME = 5     # 5s → I/O (fast, deterministic)


class AssessmentWorkflowRunner:

    def __init__(self, config: Settings, logger: logging.Logger, reporter:StatusReporter):
        self.config = config
        self.logger = logger
        self.reporter = reporter
        # progress tracking
        self._progress_initialized = False
        self._completed_step_names = set()

    def run(self):
        transcript_path  = os.path.join(PathProvider.get_project_dir(self.config), 'docs', 'project_docs',"transcript.txt")
        transcript_exists = storage_provider.file_exists(transcript_path)
        if not transcript_exists:
            self.logger.warning("Transcript file does not exist.")
            raise FileNotFoundError("Transcript file does not exist. Expected to be present at: " + transcript_path)

        return self.execute_pipeline()
    
    def execute_pipeline(self, flow_name = "start", output = None):
        try:
            config = self.get_flow_file(flow_name) 

            if config:
                self.logger.info(f"Processing flow {flow_name}")
                self.flow_name = flow_name    
                if not self._progress_initialized:
                    self._init_progress_tracker(flow_name)
                    self.reporter.report_status("Planning completed. Execution started.", state="in-progress")
                if self.config_disabled(config):
                    self.logger.info(f"Skipping, flow is disabled {flow_name}")
                    return output

                # Execute each step in the pipeline,

                if self.has_steps(config):
                        output = self.execute_steps(config["steps"], output)

                chain_items = config.get("chain", {}).get("items", [])
                for chain_item in chain_items:
                    result = self.execute_pipeline(chain_item, output)
                    if(result):
                        output = result
            else:
                self.logger.info(f"Missing flow file {flow_name}")

            if self._progress_initialized and self._completed_steps == self._total_steps:
                self.reporter.report_status(
                    "Workflow completed — 100% done"
                )
        except Exception as e:
            self.logger.info(f"Error in {flow_name}")
            self.logger.error(e, exc_info=True)
        
        return output

        

    def get_flow_file(self, flow_name):
        flow_dir = PathProvider.get_workflows_dir()
        json_path = os.path.join(flow_dir, flow_name + ".json")
        if hasattr(storage_provider, "resolve_storage_path"):
            json_path = storage_provider.resolve_storage_path(json_path)
            if file_exists(json_path, '', ''):
                # Read the JSON configuration
                config = read_from_json_file(json_path)
                return config

        json_path = os.path.join(os.path.dirname(__file__),"..", f"workflows{FLOW_VERSION}", flow_name + ".json")
        if dir_utils.file_exists(json_path, '', ''):
            # Read the JSON configuration
            config = dir_utils.read_from_json_file(json_path)
            return config

    
    def has_steps(self, config):
        return "steps" in config 
            
    def config_disabled(self, config):
        return  ("disabled" in config and config["disabled"] == True)
    
    def is_a_step(self, step):
        return "method" in step \
            and "params" in step \
                and "name" in step \
                    and ("disabled" not in step \
                         or step["disabled"] == False)
        
    def is_a_agent(self, step):
        is_agent_step = "agent_config" in step \
            and "output_key" in step \
                and "name" in step \
        
        return is_agent_step
    
    def execute_steps(self, steps, output, iteration = ""):
        for step in steps:
            if self.is_a_step(step):
                output = self.execute_step(output, step, iteration)
            elif self.is_a_agent(step):
                output = self.execute_agent(output, step, iteration)

        return output
    
    
    def get_param_from_output(self, output, param):
        if output and param in output:
            return output[param]
        return param
    
    def execute_agent(self, output, step, iteration):
        self.logger.info(f"Running as agent {step['name']}")
        
        builer = AgentBuilder(step, self.logger, args_updater=self.update_params) \
            .build_agents(tools_map=FlowMethodMap, print_diag=False) \
            .run_agents({"input": output})
        output = builer.result["outputs"][step["output_key"]]
        self.logger.info(f"Agent output: {output}")
        return output
                    

    def execute_step(self, output, step, iteration):
        self.reporter.report_status(f"Executing step {step['name']} of flow {self.flow_name}")
        step = copy.deepcopy(step)
        method_name = step["method"]
        params = step["params"]
            
            
        params = self.update_params(params, output, iteration )
            
        if method_name == "foreach_output":
            params["callback"] = self.execute_steps
            params["output_items"] = output

        self.logger.info(f"Executing method {method_name}")
        # Get the method from the method map
        method = FlowMethodMap.get(method_name, None)
        if method:
            try: 
                # Execute the method with the provided parameters
                output = method(**params)
                self.logger.info(f"Output of {step['name']}: {output}")
                # progress update (added)
                self._update_progress(step)
            except Exception as e:
                self.logger.error(f"Error executing method {method_name}")
                self.logger.error(e, exc_info=True)
        else:
            self.logger.info(f"Method {method_name} not found")
        return output

    def update_params(self, params, output = '', iteration = 0):
        context_id_exist = False

        for key, value in params.items():
            # Replace "$output" with the actual output of the previous step
            if value == "$output":
                params[key] = output
            elif value == "$context_id" :
                params[key] = self.config.context_id
            elif key == "prompt_args":
                if params[key].get("comments") == "$comments":
                    params[key]["comments"] = self.read_comments()
            elif key=="iteration":
                params[key] = iteration
            elif value == "$project_root" :
                params[key] = PathProvider.get_project_dir(self.config)
            elif isinstance(value, str) and value.startswith("$env_"):
                params[key] = os.getenv(value[5:])
            elif isinstance(value, str) and value.startswith("$"):
                params[key] = self.get_param_from_output(output, value)
        return params
    # -------------------- PROGRESS & ETA --------------------
    def _get_step_estimated_time(self, step):
        method = step.get("method", "")
        if method.startswith("run_ollama"):
            return LLM_STEP_TIME
        return IO_STEP_TIME
    def read_comments(self):
        file_path = PathProvider.get_workflow_comments_file_path(self.config)
        extracted_comments = {}
        if storage_provider.file_exists(file_path):
            extracted_comments = storage_provider.read_from_json_file(file_path)
        if not extracted_comments:
            return ""
        workflow_intent = extracted_comments.get(self.flow_name, {})
        comments = workflow_intent.get("comments", [])
        items = []
        self.logger.info(f"Read comments for {self.flow_name}")
        for cmnt in comments:
            self.logger.info(f"  - {cmnt['id']} | {cmnt['author']} | {cmnt['text']} | {cmnt['highlighted']}")
            # actual content
            block = (
                "- **Source Text for Comment:**\n"
                f" {cmnt['highlighted']}\n"
                "  **Comment:**\n"
                f" {cmnt['text']}\n"
            )
            items.append(block) 
        if items:
            comment_incorporation_rule = "\n\nComment Incorporation Rule:\nIf reviewer or developer comments are provided, you must:\n- Carefully read and interpret the comments before generating the output.\n- Treat comments as authoritative guidance for refining or correcting the generated content.\n- Apply all comment instructions logically and precisely within the generated sections.\n- Do not include the comment text itself in the output.\n- If no comments are present, proceed using only the input files and instructions above.\n\nComments (if any): {comments}".format(comments="".join(items))
            return comment_incorporation_rule
        else:
            return ""

    def _init_progress_tracker(self, flow_name):
        self._total_steps = self._count_total_steps(flow_name)
        self._completed_steps = 0

        self._total_estimated_time = self._count_total_estimated_time(flow_name)
        self._completed_estimated_time = 0

        self.reporter.report_status(
            f"Planning started for {flow_name}. Estimated execution time ~{int(self._total_estimated_time/60)} min",
            state="in-progress"
        )
        self._progress_initialized = True

    def _update_progress(self, step):
        step_name = step["name"]

        # do not count retries
        if step_name in self._completed_step_names:
            return

        self._completed_step_names.add(step_name)
        self._completed_steps += 1
        self._completed_steps = min(self._completed_steps, self._total_steps)

        percent = int((self._completed_steps / self._total_steps) * 100)

        self._completed_estimated_time += self._get_step_estimated_time(step)
        remaining = max(
            self._total_estimated_time - self._completed_estimated_time,
            0
        )

        self.reporter.report_status(
            f"Progress: {percent}% — {step_name} completed — ~{int(remaining/60)} min remaining",
            state="in-progress"
        )
    # -------------------- COUNTING --------------------
    def _count_total_steps(self, flow_name):
        config = self.get_flow_file(flow_name)
        if not config or self.config_disabled(config):
            return 0

        count = 0

        for step in config.get("steps", []):
            if self.is_a_step(step):
                count += 1
                if step.get("method") == "foreach_output":
                    for sub_step in step.get("params", {}).get("steps", []):
                        if self.is_a_step(sub_step):
                            count += 1

        for chain_item in config.get("chain", {}).get("items", []):
            count += self._count_total_steps(chain_item)

        return count

    def _count_total_estimated_time(self, flow_name):
        config = self.get_flow_file(flow_name)
        if not config or self.config_disabled(config):
            return 0

        total = 0

        for step in config.get("steps", []):
            if self.is_a_step(step):
                total += self._get_step_estimated_time(step)
                if step.get("method") == "foreach_output":
                    for sub_step in step.get("params", {}).get("steps", []):
                        if self.is_a_step(sub_step):
                            total += self._get_step_estimated_time(sub_step)

        for chain_item in config.get("chain", {}).get("items", []):
            total += self._count_total_estimated_time(chain_item)

        return total
