from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from langchain_ollama import ChatOllama
from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage, ToolMessage

from agent.state import AgentState
from agent.prompts import SYSTEM_PROMPT

from tools.rocket_jobs_tool import RocketJobsTool
from tools.resume_handler_tool import ResumeHandlerTool
from tools.job_analysis_tool import JobAnalysisTool

from config import config
from langgraph.checkpoint.memory import MemorySaver

# =====================
# Tool initialization
# =====================

rocket_tool = RocketJobsTool(
    config["site_url"]
)

resume_handler_tool = ResumeHandlerTool()

analysis_tool = JobAnalysisTool()


# =====================
# Tools
# =====================

search_jobs_tool = StructuredTool.from_function(
    func=rocket_tool.search_jobs,
    name="search_jobs",
    description="""
    Search job offers by job title.

    Use when user wants to find jobs.
    """
)


get_job_offer_tool = StructuredTool.from_function(
    func=rocket_tool.get_job_offer,
    name="get_job_offer",
    description="""
    Download and extract a job offer.

    Use when you have a job offer URL.
    """
)


get_resume_tool = StructuredTool.from_function(
    func=resume_handler_tool.get_resume,
    name="get_resume",
    description="""
    Read user's stored CV.

    Use when you need information about:
    - experience
    - skills
    - education
    - projects

    The CV already exists.
    Never ask the user to upload it.
    """
)


analyse_job_fit_tool = StructuredTool.from_function(
    func=analysis_tool.analyse_job_fit,
    name="analyse_job_fit",
    description="""
    Compare user's CV with job offer.

    Use when user asks:
    - Am I suitable candidate?
    - Do I match this job?
    - Should I apply?

    Requires:
    cv
    offer
    """
)


tools = [
    search_jobs_tool,
    get_job_offer_tool,
    get_resume_tool,
    analyse_job_fit_tool
]


# =====================
# Model
# =====================

llm = ChatOllama(
    model=config["model"],
    temperature=0
)


llm_with_tools = llm.bind_tools(
    tools
)


# =====================
# Agent node
# =====================

def agent_node(state: AgentState):
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        )
    ]

    resume = state.get("resume")
    resume_sent = state.get("resume_sent_to_llm", False)

    if resume and not resume_sent:
        messages.append(
            SystemMessage(
                content=f"""
The user resume is already loaded in memory.

IMPORTANT RULES:
- Do NOT call get_resume tool.
- Do NOT ask the user to provide the resume.
- Use this resume for:
  - career recommendations
  - job searching
  - candidate matching
  - job offer analysis


USER RESUME:

{resume}

"""
            )
        )
        # Oznacz, że CV zostało wysłane do LLM
        resume_sent = True

    elif not resume:
        messages.append(
            SystemMessage(
                content="""
The user resume is NOT loaded.

If the user asks for:
- suitable roles based on resume
- job recommendations
- candidate evaluation
- matching jobs

you MUST call get_resume first.

Do NOT ask the user to upload the resume.
The resume is stored locally and available through the tool.
"""
            )
        )

    messages.extend(state["messages"])

    # <-- TO BYŁO BRANŻOWANE, TERAZ JEST POPRAWNIE
    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response],
        "resume_sent_to_llm": resume_sent
    }


# =====================
# Tool result saving
# =====================


def save_tool_results(state: AgentState):

    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):

        if last_message.name == "get_resume":

            print(
                "Resume saved:",
                len(last_message.content)
            )

            return {
                "resume": last_message.content
            }

    return {}


# =====================
# Decision
# =====================

def should_continue(
        state: AgentState
):

    last_message = state["messages"][-1]

    if last_message.tool_calls:

        return "tools"

    return END


# =====================
# Budowa grafu
# =====================
graph = StateGraph(
    AgentState
)


graph.add_node(
    "agent",
    agent_node
)


graph.add_node(
    "tools",
    ToolNode(
        tools
    )
)


graph.add_node(
    "save_results",
    save_tool_results
)


graph.set_entry_point(
    "agent"
)


graph.add_conditional_edges(
    "agent",
    should_continue
)


graph.add_edge(
    "tools",
    "save_results"
)


graph.add_edge(
    "save_results",
    "agent"
)


memory = MemorySaver()

agent = graph.compile(
    checkpointer=memory
)
