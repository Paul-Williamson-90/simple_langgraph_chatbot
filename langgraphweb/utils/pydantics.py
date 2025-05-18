from datetime import datetime

from pydantic import BaseModel
from langchain_core.messages import AnyMessage


class ThreadMetadata(BaseModel):
    graph_id: str | None = None
    assistant_id: str | None = None
    
    
class ThreadConfigurables(BaseModel):
    model: str = "gpt-4.1-mini"
    model_provider: str = "openai"
    deep_research: bool = False
    max_research_iterations: int = 5
    
    
class ThreadConfig(BaseModel):
    configurable: ThreadConfigurables | None = None
    
    
class ThreadValues(BaseModel):
    messages: list[AnyMessage] = []
    

class Thread(BaseModel):
    thread_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: ThreadMetadata | None = None
    status: str | None = None
    config: ThreadConfig | None = None
    values: ThreadValues | None = None