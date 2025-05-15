from datetime import datetime

from langchain.chat_models import init_chat_model
from langgraph.graph import END, StateGraph

from src.state import State
from src.tools import agent_tool_kit, tool_node
from src.prompts import system_prompt


llm = init_chat_model("gpt-4o", model_provider="openai")
llm_with_tools = llm.bind_tools(agent_tool_kit)


async def call_model(state: State) -> dict:
    sys = system_prompt.format(
        time=datetime.now().isoformat()
    )

    msg = await llm_with_tools.ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
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