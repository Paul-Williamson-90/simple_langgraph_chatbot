from src.agent.tools.web_search import web_search_tool
from src.agent.tools.tool_node import BasicToolNode
from src.agent.tools.stock_fundamentals import fetch_stock_fundamentals

agent_tool_kit = [
    web_search_tool,
    fetch_stock_fundamentals
]

tool_node = BasicToolNode(agent_tool_kit)

__all__ = [
    "agent_tool_kit",
    "tool_node",
]
