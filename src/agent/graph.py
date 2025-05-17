from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableConfig
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)

from src.agent.state import State
from src.tools import agent_tool_kit
from src.agent.tool_node import BasicToolNode
from src.agent.prompts import system_prompt
from src.agent.config import Configuration


tool_node = BasicToolNode(agent_tool_kit)


def model_max_tokens(llm: BaseChatModel) -> Optional[int]:
    config = llm.model_config
    if isinstance(config, BaseModel):
        config_dict = config.model_dump()
    else:
        config_dict = config
    tokens = None
    for key in ["max_tokens", "str_max_length"]:
        tokens = config_dict.get(key, None)
        if tokens:
            break
    return tokens
            


async def call_model(state: State, config: RunnableConfig) -> dict:
    configuration = Configuration.from_runnable_config(config)
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    llm_with_tools = llm.bind_tools(agent_tool_kit)
    
    sys = system_prompt.format(
        time=datetime.now().isoformat()
    )
    max_tokens = (model_max_tokens(llm) or 128_000) - 1000
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


graph_builder = StateGraph(State, config_schema=Configuration)

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