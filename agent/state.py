from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    resume: str | None
    resume_sent_to_llm: bool
    job_offers: list[dict]
