from src.agent.tools.web_search import web_search_tool
from src.agent.tools.tool_node import BasicToolNode
from src.agent.tools.stock_fundamentals import fetch_stock_fundamentals
from src.agent.tools.stock_news import fetch_stock_related_news

agent_tool_kit = [
    web_search_tool,
    fetch_stock_fundamentals,
    fetch_stock_related_news
]

tool_node = BasicToolNode(agent_tool_kit)

__all__ = [
    "agent_tool_kit",
    "tool_node",
]
