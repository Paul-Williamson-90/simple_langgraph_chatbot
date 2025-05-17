from typing import Optional

from pydantic import BaseModel


class Section(BaseModel):
    index: int
    name: str
    description: str
    research_objectives: list[str]


class Source(BaseModel):
    title: str
    source_name: str
    url: Optional[str] = None
    
    def __str__(self) -> str:
        if self.url is None:
            return f"- {self.title} ({self.source_name})"
        return f"- [{self.title}]({self.url}) ({self.source_name})"


class CompletedSection(BaseModel):
    section_index: int
    section_title: str
    content: str
    sources: list[Source]

    def __str__(self) -> str:
        text = (
            f"## {self.section_title}\n\n"
            f"{self.content}\n\n"
        )
        if self.sources:
            text += (
                "### Sources\n"
                + "\n".join(
                    [str(source) for source in self.sources]
               )
            )
        return text
    
    
    
class Brief(BaseModel):
    research_topic: str
    research_high_level_objectives: str
    section: Section
    
    def __str__(self) -> str:
        text = (
            f"Research Topic: {self.research_topic}\n"
            f"Research High Level Objectives: {self.research_high_level_objectives}\n"
            f"Section Index: {self.section.index}\n"
            f"Section Topic: {self.section.name}\n"
            f"Section Description: {self.section.description}\n"
            f"Section Research Objectives: {self.section.research_objectives}\n"
        )
        return text