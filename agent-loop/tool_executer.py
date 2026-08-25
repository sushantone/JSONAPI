from typing import Any, Dict, List, Optional
from src.agents.agent_tool import AgentTool

class ToolExecutor:
    """Manages tool registration and execution."""

    def __init__(self, logger, tools: Optional[List[AgentTool]] = None):
        self.logger = logger
        self.tools: Dict[str, AgentTool] = {}
        if tools:
            for tool in tools:
                self.register_tool(tool)

    def register_tool(self, tool: AgentTool):
        """Registers a tool."""
        if tool.name in self.tools:
            self.logger.info(f"Tool '{tool.name}' is already registered.")
        self.tools[tool.name] = tool

    def execute(self, tool_name: str, *args, **kwargs) -> Any:
        """Executes a tool by name with given arguments."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found.")
        try:
            return tool.invoke(*args, **kwargs)
        except Exception as e:
            raise ValueError(f"Error executing tool '{tool_name}': {e}") from e

    def get_tool_names(self) -> List[str]:
        """Returns a list of all registered tool names."""
        return list(self.tools.keys())

    def get_tool_details(self) -> str:
        """Returns details of all registered tools."""
        tools_info = [f"{tool.name}: {tool.description} Args schema: {tool.args}" for tool in self.tools.values()]
        return '\n'.join(tools_info)
