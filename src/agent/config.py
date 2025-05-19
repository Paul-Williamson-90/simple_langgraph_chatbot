import os
from typing import Any, Optional

from dataclasses import dataclass, fields
from langchain_core.runnables import RunnableConfig

from src.agent.prompts import (
    system_prompt,
    report_planner_instructions, 
    report_conclusion_instructions,
    report_intro_instructions,
    deep_research_system_instruction
)


@dataclass(kw_only=True)
class Configuration:
    model: str = "gpt-4.1-mini"
    model_provider: str = "openai"
    deep_research: bool = False
    max_research_iterations: int = 5
    system_prompt: str = system_prompt
    report_planner_instructions: str = report_planner_instructions
    report_conclusion_instructions: str = report_conclusion_instructions
    report_intro_instructions: str = report_intro_instructions
    deep_research_system_instruction: str = deep_research_system_instruction
    
    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})