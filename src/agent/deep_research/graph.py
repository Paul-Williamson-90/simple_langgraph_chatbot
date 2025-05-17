import json
from typing import Literal
import logging

from langgraph.graph import START, END, StateGraph
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from langchain_core.messages import AIMessage, ToolMessage

from src.agent.deep_research.state import SectionState, SectionOutputState
from src.tools import agent_tool_kit
from src.agent.deep_research.pydantics import CompletedSection, Brief, Section
from src.agent.config import Configuration
from src.agent.deep_research.prompts import system_instruction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def brief_from_state(state: SectionState) -> str:
    if isinstance(state.section, dict):
        state.section = Section(**state.section)
    brief = Brief(
        research_topic=state.report_topic,
        research_high_level_objectives=state.report_high_level_objectives,
        section=state.section,
    )
    return str(brief)


def _get_system_instruction(state: SectionState, current_step: str) -> str:
    tools_available = [
        {
            "tool_name": tool.name,
            "tool_description": tool.description
        } for tool in agent_tool_kit
    ]
    brief = brief_from_state(state)
    sys = system_instruction.format(
        current_step=current_step,
        tools_available=json.dumps(tools_available, indent=2),
        brief=brief,
    )
    return sys


async def reasoning_step(state: SectionState, config: RunnableConfig) -> dict:
    configuration = Configuration.from_runnable_config(config)
    logger.info(str(state))
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    sys = _get_system_instruction(
        state=state, current_step="Reflection Step"
    )
    msgs = state.messages
    msg = await llm.ainvoke(
        [{"role": "system", "content": sys}, *msgs]
    )
    return {"messages": [msg]}


async def tool_selection_step(state: SectionState, config: RunnableConfig) -> dict:
    configuration = Configuration.from_runnable_config(config)
    
    state.iterations += 1
    if state.iterations > configuration.max_research_iterations:
        msg = AIMessage(
            content="I have spent enough time researching and should move on to completing the section."
        )
        return {"messages": [msg]}
    
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    llm_with_tools = llm.bind_tools(agent_tool_kit)
    sys = _get_system_instruction(
        state=state, current_step="Tool Selection Step"
    )
    msgs = state.messages
    msg = await llm_with_tools.ainvoke(
        [{"role": "system", "content": sys}, *msgs]
    )
    return {"messages": [msg]}


def route_tools_message(state: SectionState) -> str:
    msg = state.messages[-1]
    if msg.tool_calls:
        return "tools"
    return "complete_section_step"


async def tool_node(state: SectionState, config: RunnableConfig) -> dict:
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


async def complete_section_step(state: SectionState, config: RunnableConfig) -> Command[Literal["__end__"]]:
    configuration = Configuration.from_runnable_config(config)
    llm = init_chat_model(
        model=configuration.model, 
        model_provider=configuration.model_provider
    )
    
    structured_llm = llm.with_structured_output(
        schema=CompletedSection
    )
    
    sys = _get_system_instruction(
        state=state, current_step="Writing Step"
    )
    
    msgs = state.messages
    section = await structured_llm.ainvoke(
        [{"role": "system", "content": sys}, *msgs]
    )
    
    if not isinstance(section, CompletedSection):
        raise ValueError(
            f"Expected CompletedSection, got {type(section)}"
        )
        
    return Command(
        update={"completed_sections": [section]},
        goto=END
    )
    
    
deep_researcher_build = StateGraph(SectionState, output=SectionOutputState, config_schema=Configuration)

deep_researcher_build.add_node("reasoning_step", reasoning_step)
deep_researcher_build.add_node("tool_selection_step", tool_selection_step)
deep_researcher_build.add_node("complete_section_step", complete_section_step)
deep_researcher_build.add_node("tools", tool_node)

deep_researcher_build.add_edge(START, "reasoning_step")
deep_researcher_build.add_edge("reasoning_step", "tool_selection_step")
deep_researcher_build.add_conditional_edges(
    "tool_selection_step", 
    route_tools_message,
    {
        "tools": "tools",
        "complete_section_step": "complete_section_step"
    }
)
deep_researcher_build.add_edge("tools", "reasoning_step")