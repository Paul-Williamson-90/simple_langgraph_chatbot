from datetime import datetime
from typing import Optional
import json

from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langgraph.graph import START, END, StateGraph
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)

from src.agent.state import State
from src.tools import agent_tool_kit
from src.agent.prompts import system_prompt
from src.agent.config import Configuration


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


def route_start(state: State, config: RunnableConfig):
    configuration = Configuration.from_runnable_config(config)
    if configuration.deep_research is True:
        raise NotImplementedError(
            "Deep research is not implemented yet."
        )
    return "call_model"


async def tool_node(state: State, config: RunnableConfig):
    if messages := state.messages:
        message = messages[-1]
    else:
        raise ValueError("No message found in input")
    tools_by_name = {
        tool.name: tool for tool in agent_tool_kit
    }
    outputs = []
    for tool_call in message.tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(
            tool_call["args"]
        )
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}


async def generate_report_plan(state: State, config: RunnableConfig):
    return 


graph_builder = StateGraph(State, config_schema=Configuration)

graph_builder.add_node("call_model", call_model)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("generate_report_plan", generate_report_plan)

graph_builder.add_conditional_edges(
    START,
    route_start,
    {"call_model": "call_model", "generate_report_plan": "generate_report_plan"}
)
graph_builder.add_conditional_edges(
    "call_model",
    route_message,
    {"tools": "tools", END: END}
)
graph_builder.add_edge("tools", "call_model")

graph_builder.add_edge("generate_report_plan", END)

graph = graph_builder.compile()
graph.name = "Tool Agent"

__all__ = ["graph"]