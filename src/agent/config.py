import os
from typing import Any, Optional

from dataclasses import dataclass, fields
from langchain_core.runnables import RunnableConfig


@dataclass(kw_only=True)
class Configuration:
    model: str = "gpt-4o"
    model_provider: str = "openai"
    
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