import json
from typing import Any

from typer import prompt

from src.providers.llm_provider import LLMProvider, PromptNames

supported_agents = [
    {
        "name": "orchestrator",
        "description": "You need to orchestrate the workflow and handoff between different agents based on the work item and the output from other agents. You should also provide the final output based on the work item and the output from other agents. You should be responsible for providing the final output of the workflow based on the work item and the output from other agents.",
    },
    {
        "name": "legacy_code_analyzer",
        "description": "Plan on how to analyzes legacy code to identify components and dependencies",
    },
    {
        "name": "domain_extractor",
        "description": "Plan on how to extract domain models and entities from the legacy codebase",
    },
    {
        "name": "product_owner",
        "description": "Plan to provides requirements clarification and acceptance criteria for the domains extracted from the legacy codebase",
    },
    {
        "name": "api_developer",
        "description": "Plan on how to develops APIs based on the extracted domain models and requirements",
    },
    {
        "name": "code_reviewer",
        "description": "Plan on how to reviews the generated code for quality and adherence to requirements",
    },
    {
        "name": "test_writer",
        "description": "Plan on how to writes tests for the generated code to ensure functionality and reliability",
    },
    {
        "name": "documentation_writer",
        "description": "Plan on how to creates documentation for the generated APIs and codebase",
    },
]


class AgentConfigBuilder:
    def generate_agent_config(
        self, work_item: str, available_agents: list[Any] = supported_agents
    ) -> dict[str, Any]:
        """
        Generate an agent workflow configuration based on a work item description.

        Args:
            work_item: A string describing the work item/task to be accomplished
            available_agents: List of available agent names (e.g., ['po', 'coder', 'reviewer'])

        Returns:
            A dictionary containing the agent_config and run_config for the workflow

        Example:
            >>> agents = ['po', 'project_manager', 'coder', 'reviewer']
            >>> config = generate_agent_config("Build a REST API for user management", agents, my_llm_call)
        """

        llm_input = self._build_prompt(work_item, available_agents)

        # Call LLM to generate the configuration
        llm_response = LLMProvider().invoke_llm(llm_input)

        # Parse and validate the response
        config = self._parse_llm_response(llm_response)

        return config

    def _build_prompt(self, work_item: str, available_agents: list[str]) -> str:
        """
        Build the prompt for the LLM to generate agent configuration.

        Args:
            work_item: Description of the work item
            available_agents: List of available agent names

        Returns:
            Formatted prompt string for the LLM
        """

        example_config = {
            "agent_config": {
                "project_manager": {
                    "prompt": "Provide only the details of the requirement and mention clear acceptance criteria.  \n\n** DO NOT PROVIDE ANY CODE **. If the review feedback is provided and it is fine, make the work completed. \n\n **Requirement** : {requirement}. \n\n**Review Comments** : {reviewer_plan}",
                    "output_key": "project_manager_plan",
                    "hand_off": [
                        {"NO": "coder", "NO.": "coder", "YES": "po", "YES.": "po"}
                    ],
                    "hand_off_condition": "Respond as YES if no major of the issue mentioned in the review comments. \n\n Respond as NO if some critical cases are not handled or comments are 'Not Available'. \n\n**Review Comments**: {reviewer_plan}",
                    "initial_value": "",
                },
                "coder": {
                    "prompt": "Develop code based on the requirement and provide the code. You should fix the code based on review comments, if provided. Please also mention what you changed and why. Also for each review comments provide YES or NO if those comments are addressed. \n\n**Requirement** : {project_manager_plan} \n\n**Review Comments** : {reviewer_plan} \n\n **Code** : {coder_plan}",
                    "output_key": "coder_plan",
                    "hand_off": [{"*": "reviewer"}],
                    "initial_value": "Not Available",
                },
                "reviewer": {
                    "prompt": "Review the code and provide the review comments. Ensure code is well documented and follow python standards. Ensure Unit Tests are also added to the generated code, consider critical issue if Unite Tests are missing.  Only return  the list of issues / suggestions or say no issues found. As a reviewer you should only give suggestions and DO NOT DO ANY CODING. \n\n**Requirement** : {project_manager_plan} \n\n**Code** : {coder_plan} \n\n",
                    "output_key": "reviewer_plan",
                    "hand_off": [
                        {
                            "NO": "coder",
                            "YES": "project_manager",
                            "NO.": "coder",
                            "YES.": "project_manager",
                        }
                    ],
                    "hand_off_condition": "Respond as YES if no major of the issue found. \n\n Respond as NO if some critical cases are not handled or performance issue exists or unittests are missing or comments are 'Not Available'. \n\n**Review Comments** : {reviewer_plan}",
                    "initial_value": "Not Available",
                },
            },
            "run_config": {"recursion_limit": 50},
        }
        llm_input = LLMProvider.get_prompt(PromptNames.agent_config_builder)
        llm_input["messages"][1]["content"] = llm_input["messages"][1][
            "content"
        ].format(
            work_item=work_item,
            available_agents=json.dumps(available_agents, indent=2),
            example_config=json.dumps(example_config, indent=2),
        )

        return llm_input

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """
        Parse and validate the LLM response into a configuration dictionary.

        Args:
            response: Raw string response from the LLM

        Returns:
            Parsed configuration dictionary

        Raises:
            ValueError: If the response cannot be parsed as valid JSON
            KeyError: If required keys are missing from the configuration
        """

        # Clean up the response - remove markdown code blocks if present
        cleaned_response = response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        cleaned_response = cleaned_response.strip()

        try:
            config = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

        # Validate required keys
        if "agent_config" not in config:
            raise KeyError("Missing required key: 'agent_config'")

        if "run_config" not in config:
            # Add default run_config if missing
            config["run_config"] = {"recursion_limit": 50}

        # Validate agent_config structure
        self._validate_agent_config(config["agent_config"])

        return config

    def _validate_agent_config(self, agent_config: dict[str, Any]) -> None:
        """
        Validate the agent configuration structure.

        Args:
            agent_config: The agent configuration dictionary to validate

        Raises:
            ValueError: If the configuration is invalid
        """

        if not agent_config:
            raise ValueError("agent_config cannot be empty")

        entry_points = []

        for agent_name, agent_def in agent_config.items():
            # Check for entry point
            if agent_def.get("entry_point", False):
                entry_points.append(agent_name)

            # Validate required fields
            if "prompt" not in agent_def:
                raise ValueError(
                    f"Agent '{agent_name}' missing required field: 'prompt'"
                )

            if "hand_off" not in agent_def:
                raise ValueError(
                    f"Agent '{agent_name}' missing required field: 'hand_off'"
                )

            # Validate hand_off is a list
            if not isinstance(agent_def["hand_off"], list):
                raise ValueError(f"Agent '{agent_name}' hand_off must be a list")

        # Ensure exactly one entry point
        if len(entry_points) == 0:
            raise ValueError("No entry_point defined in agent_config")

        if len(entry_points) > 1:
            raise ValueError(f"Multiple entry_points defined: {entry_points}")
