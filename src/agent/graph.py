from datetime import datetime

from langchain.chat_models import init_chat_model
from langgraph.graph import END, StateGraph
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)

from src.agent.state import State
from src.tools import agent_tool_kit, tool_node
from src.agent.prompts import system_prompt


llm = init_chat_model("gpt-4o", model_provider="openai")
llm_with_tools = llm.bind_tools(agent_tool_kit)


async def call_model(state: State) -> dict:
    sys = system_prompt.format(
        time=datetime.now().isoformat()
    )
    max_tokens = (llm.model_config.str_max_length or 128_000) - 1000
    msgs = trim_messages(
        state.messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=max_tokens,
        start_on="human",
        include_system=True,
    )
    msg = await llm_with_tools.ainvoke(
        [{"role": "system", "content": sys}, *msgs],
    )
    return {"messages": [msg]}


def route_message(state: State):
    msg = state.messages[-1]
    if msg.tool_calls:
        return "tools"
    return END


graph_builder = StateGraph(State)

graph_builder.add_node("call_model", call_model)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge("__start__", "call_model")
graph_builder.add_conditional_edges(
    "call_model",
    route_message,
    {"tools": "tools", END: END}
)
graph_builder.add_edge("tools", "call_model")

graph = graph_builder.compile()
graph.name = "Tool Agent"

__all__ = ["graph"]