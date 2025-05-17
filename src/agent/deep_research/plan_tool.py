from langchain_core.tools import tool

from src.agent.deep_research.pydantics import Section


@tool("submit_research_report_plan")
def submit_research_report_plan(
    report_topic: str,
    report_high_level_objectives: str,
    report_structure: list[Section],
) -> bool:
    """
    Submit the research report plan to researchers for executing the plan.
    
    Args:
        report_topic (str): The topic of the report.
        report_high_level_objectives (str): The high-level objectives of the report.
        report_structure (list[Section]): The structure of the report, including sections and their details.
    """
    # Note this is a dummy tool to hack tool calling as a structured output
    # without blocking free-text generation.
    return True