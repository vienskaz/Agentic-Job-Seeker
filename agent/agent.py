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
from tools.resume_tailoring_tool import ResumeTailoringTool

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

tailoring_tool = ResumeTailoringTool()


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

    Use when you need:
    - experience
    - skills
    - education
    - projects

    The CV already exists locally.
    Never ask user to upload it.
    """
)


analyse_job_fit_tool = StructuredTool.from_function(
    func=analysis_tool.analyse_job_fit,
    name="analyse_job_fit",
    description="""
    Use only when you used get_resume() before.
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


resume_tailoring_tool = StructuredTool.from_function(
    func=tailoring_tool.tailor_resume_to_job,
    name="tailor_resume_to_job",
    description="""
    Use only when you used get_resume() before.
    Tailor candidate's CV to the job vacancy so that it’s a better fit, 
    
    but don’t make up experience – take everything that’s in 
    
    candidate's CV and phrase it more effectively.

    Requires:
    cv
    offer
    """
)


tools = [
    search_jobs_tool,
    get_job_offer_tool,
    get_resume_tool,
    analyse_job_fit_tool,
    resume_tailoring_tool
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


def agent_node(
        state: AgentState
):

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        )
    ]

    resume = state.get(
        "resume"
    )

    resume_sent = state.get(
        "resume_sent_to_llm",
        False
    )

    if resume and not resume_sent:

        messages.append(
            SystemMessage(
                content=f"""
The user resume is already loaded in memory.

IMPORTANT RULES:
- Do NOT call get_resume.
- Do NOT ask user to upload resume.
- Use this resume for:
  - career recommendations
  - job searching
  - candidate matching
  - job analysis


USER RESUME:

{resume}

"""
            )
        )

        resume_sent = True

    elif not resume:

        messages.append(
            SystemMessage(
                content="""
The user resume is NOT loaded.

If user asks for:
- job recommendations
- finding jobs
- candidate evaluation
- matching offers

you MUST call get_resume first.

Do NOT ask user to upload CV.
"""
            )
        )

    messages.extend(
        state["messages"]
    )

    response = llm_with_tools.invoke(
        messages
    )

    return {
        "messages": [
            response
        ],
        "resume_sent_to_llm": resume_sent
    }


# =====================
# Tool result saving
# =====================


def save_tool_results(
        state: AgentState
):

    last_message = state["messages"][-1]

    if isinstance(
        last_message,
        ToolMessage
    ):

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
# Graph
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


# =====================
# Memory
# =====================


memory = MemorySaver()


agent = graph.compile(
    checkpointer=memory
)
