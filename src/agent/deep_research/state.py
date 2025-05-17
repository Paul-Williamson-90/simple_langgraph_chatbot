from dataclasses import dataclass

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated

from src.agent.deep_research.pydantics import CompletedSection, Section


@dataclass(kw_only=True)
class SectionState:
    """Main graph state."""
    report_topic: str
    report_high_level_objectives: str
    section: Section
    messages: Annotated[list[AnyMessage], add_messages]
    """The messages in the conversation."""
    iterations: int = 0
    
    
@dataclass(kw_only=True)
class SectionOutputState:
    completed_sections: list[CompletedSection] 