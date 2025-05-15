from src.tools.web_search import web_search_tool
from src.tools.tool_node import BasicToolNode


agent_tool_kit = [
    web_search_tool
]

tool_node = BasicToolNode(agent_tool_kit)

__all__ = [
    "agent_tool_kit",
    "tool_node",
]