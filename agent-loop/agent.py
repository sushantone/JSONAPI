from typing import Dict, Optional
from src.providers.llm_provider import LLMProvider, PromptNames
from src.agents.tool_executer import ToolExecutor
from langchain_core.runnables.base import Runnable
from langchain_core.runnables.config import RunnableConfig
#from langchain.agents.output_parsers import ReActSingleInputOutputParser
import json
import re

class Agent(Runnable):

    def __init__(self, name, config, logger, tools_map: Dict[str, any] = None, args_updater = None):
        
        self.hand_off_condition = config.get("hand_off_condition", None)
        self.args_updater = args_updater
        self.tool_history = []
        self.name = name
        self.logger = logger
        self.executor = ToolExecutor(self.logger)
        self.prompt = config["prompt"]
        self.tool_names = config.get("tools", [])
        self.output_key = config.get("output_key", self.name + "_output")
        self.tools = []
        # Register and convert tools
        if self.tool_names:
            for tool_name in self.tool_names:
                tool = tools_map[tool_name]
                self.tools.append(tool)
                self.executor.register_tool(tool)
            # self.function_calls = [ToolsMap[tool].to_openai_function_call_definition() for tool in tools]

    def is_satisfied(self, state):
        hand_off_condition = self.hand_off_condition
        if hand_off_condition == None:
            return True
        status = self.router(state["outputs"], hand_off_condition)
        state["status"] = status
        return status

    def router(self, outputs, router_prompt):
        prompt = router_prompt.format(**outputs)
        prompt_json = LLMProvider.get_prompt(PromptNames.router_prompt)
        prompt_json["messages"][1]["content"] = prompt_json["messages"][1][
            "content"
        ].format(**{"prompt": prompt}, **outputs)
        response = LLMProvider().invoke_llm(prompt_json)
        self.logger.info(f"Agent '{self.name}' Assessment: {response} \n**********\n\n")
        try:
            result = json.loads(response)
            return result.get("workdone", "NO") if result.get("workdone", "NO") == "YES" else "NO" 
        except :
            return "NO"

    def invoke(self, state, config: Optional[RunnableConfig] = None):
        prompt = self.prompt.format(**state["outputs"])

        result = self.run(
            {"role": "user", "content": prompt},
            {"role": "system", "content": f"You are a helpful {self.name}"},
        )

        state["outputs"][self.output_key] = result
        self.logger.info(
            f"Agent: {self.name} \n-------------\n Output: {result} \n**********\n\n"
        )
        # state['chat_history'].append(BaseMessage(type="assistant", content=result))
        return state

    def run(self, user_message: Dict[str, str], system_message: Dict[str, str]):
        """Generates responses, manages tool calls, and updates memory."""
        if (
            self.tools != None
            and len(self.tools) > 0):

            response = self.tool_query(user_message, system_message)
        else:
            response = LLMProvider().invoke_llm(
                {"messages": [system_message, user_message]}
            )

        return response
    
    def tool_query(self, user_message: Dict[str, str], system_message: Dict[str, str]):

        msg = (
                f"""\n\n 
Available tools: {self.executor.get_tool_details()} 

You MUST return the output in the EXACT format below:
Thought: A single line describing the reasoning process.
Action: [Tool Name] (must be one of the available tools: {self.executor.get_tool_names()}).
Action Input: [Arguments in PURE JSON format]. If no input is required, return `null`.

Example:
Thought: Analyzing the input.
Action: tool1
Action Input: {{"key": "value"}}
            
RETURN THE OUTPUT IN THE EXACT FORMAT ABOVE AS STRING and NOT JSON.
DO NOT ADD ANY ADDITIONAL TEXT, CODE IDENTIFIER OR EXPLANATION etc.
        """)
        system_message["content"] = msg
        response = LLMProvider().invoke_llm(
            {"messages": [system_message, user_message], "temperature": 0.0}
        )

        parsed_response = self.parse_response(response)

        if parsed_response != None:
            response = parsed_response
        return response

    def _extract_tool_from_response(self, response):
        if hasattr(response, "tool"):
            return response.tool, response.tool_input

        if not isinstance(response, str):
            return "", ""

        action_match = re.search(r"^Action:[ \t]*([^\n\r]*)", response, re.MULTILINE)
        input_match = re.search(r"^Action Input:[ \t]*([^\n\r]*)", response, re.MULTILINE)
        tool_name = action_match.group(1).strip() if action_match else ""
        tool_input = input_match.group(1).strip() if input_match else ""
        return tool_name, tool_input

    def parse_response(self, response) -> bool:
        """Executes tool calls suggested by the LLM and updates tool history."""

        tool_name = ""
        try:
            tool_name, tool_args = self._extract_tool_from_response(response)
            if tool_args != "None" and tool_args != "":
                try:
                    match = re.search(r'\{.*\}', tool_args.replace("\n",""))
                    if match:
                        tool_args = match.group()
                    tool_args = json.loads(tool_args)
                except:
                    tool_args = {}
                    self.logger.info(f"Failed to parse tool arguments: {tool_args}")

            if tool_name != "":
                if self.args_updater :
                    tool_args = self.args_updater(tool_args)
                return self.executor.execute(tool_name, tool_args)
        except Exception as e:
            self.logger.info(
                f"No tool required or error in tool execution '{tool_name}': {e}"
            )

        return None
