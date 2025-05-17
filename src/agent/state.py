from dataclasses import dataclass, field
import operator

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated

from src.agent.deep_research.pydantics import CompletedSection


@dataclass(kw_only=True)
class State:
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages]
    """The messages in the conversation."""
    completed_sections: list[CompletedSection] = field(default_factory=list)
    report_topic: str = ""
    report_high_level_objectives: str = ""
    
    
@dataclass(kw_only=True)
class InputState:
    messages: Annotated[list[AnyMessage], add_messages]
    """The messages in the conversation."""