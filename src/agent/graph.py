from datetime import datetime
from typing import Optional, Literal
import json

from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from langchain_core.language_models import BaseChatModel
from langgraph.graph import START, END, StateGraph
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.constants import Send
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)
from langgraph.pregel import RetryPolicy

from src.agent.state import State, InputState
from src.tools import agent_tool_kit
from src.agent.config import Configuration
from src.agent.deep_research.graph import deep_researcher_build
from src.agent.deep_research.plan_tool import submit_research_report_plan
from src.agent.deep_research.pydantics import CompletedSection


def brief_from_state(state: State) -> str:
    text = f"Research Topic: {state.report_topic}\n"
    text += f"High Level Objectives: {state.report_high_level_objectives}\n"
    return text


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


async def start_node(state: State, config: RunnableConfig) -> dict:
    last_message = state.messages[-1]
    return {"internal_messages": [last_message]}


async def call_model(state: State, config: RunnableConfig) -> Command[Literal[END, "tools"]]:
    configuration = Configuration.from_runnable_config(config)
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    llm_with_tools = llm.bind_tools(agent_tool_kit)
    
    sys = configuration.system_prompt.format(
        time=datetime.now().isoformat()
    )
    max_tokens = (model_max_tokens(llm) or 128_000) - 1000
    msgs = trim_messages(
        state.internal_messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=max_tokens,
        start_on="human",
        include_system=True,
    )
    msg = await llm_with_tools.ainvoke(
        [{"role": "system", "content": sys}, *msgs],
    )
    if msg.tool_calls:
        return Command(
            goto="tools",
            update={"internal_messages": [msg]},
        )
    return Command(
        goto=END,
        update={
            "messages": [msg], 
            "internal_messages": [msg]
        },
    )


def route_start(state: State, config: RunnableConfig) -> str:
    configuration = Configuration.from_runnable_config(config)
    if configuration.deep_research is True:
        return "generate_report_plan"
    return "call_model"


async def tool_node(state: State, config: RunnableConfig) -> dict:
    if messages := state.internal_messages:
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
    return {"internal_messages": outputs}


async def generate_report_plan(state: State, config: RunnableConfig) -> Command[Literal[END, "trigger_build"]]:
    configuration = Configuration.from_runnable_config(config)
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    llm_with_tools = llm.bind_tools([submit_research_report_plan])
    sys = configuration.report_planner_instructions
    max_tokens = (model_max_tokens(llm) or 128_000) - 1000
    msgs = trim_messages(
        state.internal_messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=max_tokens,
        start_on="human",
        include_system=True,
    )
    msg = await llm_with_tools.ainvoke(
        [{"role": "system", "content": sys}, *msgs],
    )

    report_topic = ""
    report_high_level_objectives = ""
    if hasattr(msg, "tool_calls"):
        tool_calls = msg.tool_calls
        if tool_calls:
            tool_call = tool_calls[0]
            report_plan = tool_call.get("args", {})
            if not isinstance(report_plan, dict): 
                raise ValueError(
                    "Report plan is not a dictionary"
                )
            report_topic = report_plan.get("report_topic", "")
            report_high_level_objectives = report_plan.get("report_high_level_objectives", "")
            
    if msg.tool_calls:
        return Command(
            goto="trigger_build",
            update={
                "internal_messages": [msg], 
                "report_topic": report_topic, 
                "report_high_level_objectives": report_high_level_objectives
            },
        )
    return Command(
        goto=END,
        update={
            "messages": [msg], 
            "internal_messages": [msg], 
            "report_topic": report_topic, 
            "report_high_level_objectives": report_high_level_objectives
        },
    )


def trigger_build(state: State) -> Command[Literal["build_section"]]:
    msg = state.internal_messages[-1]
    if msg.tool_calls:
        sends = _prepare_research_topics(state)
        return Command(goto=sends)
    else:
        raise ValueError(
            "No tool calls found in message"
        )


def _prepare_research_topics(state: State) -> list[Send]:
    msg = state.internal_messages[-1]
    research_plan = msg.tool_calls[0].get("args", None)
    
    if not research_plan:
        raise ValueError("No research plan found in tool call")
    
    report_topic = research_plan.get("report_topic", None)
    report_high_level_objectives = research_plan.get("report_high_level_objectives", None)
    report_structure = research_plan.get("report_structure", None)
    
    if not all([report_topic, report_high_level_objectives, report_structure]):
        raise ValueError("Missing required fields in research plan")

    sends = [
        Send(
            "build_section", {
                "report_topic": report_topic, 
                "report_high_level_objectives": report_high_level_objectives, 
                "section": section
            }
        ) 
        for section in report_structure
    ]
    
    return sends


def format_sections(completed_sections: list[CompletedSection]) -> list[str]:
    return [str(section) for section in completed_sections]


async def write_conclusion(state: State, config: RunnableConfig) -> dict:
    configuration = Configuration.from_runnable_config(config)
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    section_index = len(state.completed_sections)
    completed_sections = state.completed_sections
    completed_sections.sort(key=lambda x: x.section_index)
    completed_report_sections = format_sections(completed_sections)
    sys = configuration.report_conclusion_instructions.format(
        completed_report_sections="\n".join(completed_report_sections),
        brief=brief_from_state(state),
    )
    content = await llm.ainvoke(
        [{"role": "system", "content": sys}],
    )
    conclusion_section = CompletedSection(
        section_index=section_index,
        section_title="Conclusion",
        content=content.content,
        sources=[],
    )
    return {"completed_sections": [conclusion_section]}


async def write_intro(state: State, config: RunnableConfig) -> dict:
    configuration = Configuration.from_runnable_config(config)
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    section_index = -1
    completed_sections = state.completed_sections
    completed_sections.sort(key=lambda x: x.section_index)
    completed_report_sections = format_sections(completed_sections)
    sys = configuration.report_intro_instructions.format(
        completed_report_sections="\n".join(completed_report_sections),
        brief=brief_from_state(state),
    )
    content = await llm.ainvoke(
        [{"role": "system", "content": sys}],
    )
    intro_section = CompletedSection(
        section_index=section_index,
        section_title="Introduction",
        content=content.content,
        sources=[],
    )
    return {"completed_sections": [intro_section]}


async def compile_final_report(state: State, config: RunnableConfig) -> dict:
    completed_sections = state.completed_sections
    completed_sections.sort(key=lambda x: x.section_index)
    completed_report_sections = format_sections(completed_sections)
    report_content = "\n\n".join(completed_report_sections)
    msg = AIMessage(
        content=f"# {state.report_topic.title()}\n{report_content}"
    )
    return {"messages": [msg], "internal_messages": [msg]}


graph_builder = StateGraph(State, input=InputState, config_schema=Configuration)

graph_builder.add_node("start_node", start_node, retry=RetryPolicy())
graph_builder.add_node("call_model", call_model, retry=RetryPolicy())
graph_builder.add_node("tools", tool_node, retry=RetryPolicy())
graph_builder.add_node("generate_report_plan", generate_report_plan, retry=RetryPolicy())
graph_builder.add_node("trigger_build", trigger_build, retry=RetryPolicy())
graph_builder.add_node("build_section", deep_researcher_build.compile(debug=True))
graph_builder.add_node("compile_final_report", compile_final_report, retry=RetryPolicy())
graph_builder.add_node("write_conclusion", write_conclusion, retry=RetryPolicy())
graph_builder.add_node("write_intro", write_intro, retry=RetryPolicy())

graph_builder.add_edge(START, "start_node")
graph_builder.add_conditional_edges(
    "start_node",
    route_start,
    {"call_model": "call_model", "generate_report_plan": "generate_report_plan"}
)
graph_builder.add_edge("tools", "call_model")
graph_builder.add_edge("build_section", "write_conclusion")
graph_builder.add_edge("write_conclusion", "write_intro")
graph_builder.add_edge("write_intro", "compile_final_report")
graph_builder.add_edge("compile_final_report", END)

graph = graph_builder.compile(debug=True)
graph.name = "Tool Agent"

__all__ = ["graph"]