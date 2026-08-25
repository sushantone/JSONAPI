import json
import logging
from typing import TypedDict
from langgraph.graph import StateGraph
from src.agents.agent import Agent

class AgentBuilder:

    def __init__(self, config, logger = logging.getLogger(__name__), args_updater = None):
        self.app = None
        self.args_updater = args_updater
        self.logger = logger
        self.agent_config = config["agent_config"]
        self.run_config = config.get("run_config", {"recursion_limit": 10})
        self.tools_map = {}

    class AgentState(TypedDict):
        status: str
        outputs: dict = {}

        def __init__(self):
            for _, config in self.agent_config.items():
                self.outputs[config["output_key"]] = ""

    def build_agent_workflow(self, tools_map: dict[str,any] = None):
        """
        Build the agent workflow using the provided configuration.
        """
        # Create a state graph
        self.workflow = StateGraph(self.AgentState)

        # Add agents to the workflow
        for agent_name, config in self.agent_config.items():

            agent = Agent(name=agent_name, config=config, tools_map=tools_map, logger=self.logger, args_updater=self.args_updater)

            self.workflow.add_node(agent_name, agent)

            if config.get("entry_point", False):
                self.workflow.set_entry_point(agent_name)

            for hand_off in config.get("hand_off", []):
                hands_off = hand_off.get("*", '')
                if hands_off != '':
                    if isinstance(hands_off, str):
                        hands_off = [hands_off]
                    for hand_off_name in hands_off:
                            self.workflow.add_edge(agent_name, hand_off_name)   
                else :
                    try:
                    #for hand_off_name in hand_off:
                        self.workflow.add_conditional_edges(
                            agent_name,
                            agent.is_satisfied,
                            hand_off,
                        )
                    except Exception as e:
                        self.logger.info(f"Error adding conditional edges for agent {agent_name}, skipping: {e}")

        return self.workflow.compile()

    def build_agents(self, print_diag = False, tools_map: dict[str,any] = None):

        self.app = self.build_agent_workflow(tools_map=tools_map)
        if print_diag:
            self.logger.info(self.app.get_graph().draw_ascii())

        self.state = {
            "status": "NO",
            "outputs": {
            },
        }

        for name, config in self.agent_config.items():
            self.state["outputs"][config["output_key"] if "output_key" in config else name + "_output"] = config.get("initial_value","")

        return self

    def run_agents(self, input_partial: dict[str, str]):
        """
        Run the agents in the workflow.
        """
        result = ""
        for key in input_partial.keys():
            self.state["outputs"][key] = input_partial[key]
        try: 
            for s in self.app.stream(self.state, config = self.run_config):
                result = list(s.values())[0]
            # results.append(result)
            # print(result)
            # print('\n-----\n')
        except Exception as e:
            self.logger.info(f"Error: {e}")
        self.result = result
        self.logger.info(json.dumps(result, indent=4))
        return self
