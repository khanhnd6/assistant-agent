from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from tools.analysis_tools import filter_records_tool, plot_records_tool
from tools.record_tools import create_records_tool, retrieve_records_tool, delete_record_tool, update_record_tool
from tools.context_tools import get_schema_tool, get_user_profile_tool
from tools.research_tools import research_tool
from agents import Agent, ModelSettings
from utils.context import UserContext
from utils.date import current_time
from instructions import *

model="gpt-4o-mini"

schema_agent = Agent[UserContext](
    name="schema_agent",
    model=model,
    instructions=SCHEMA_AGENT_INSTRUCTION,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
)

record_agent = Agent[UserContext](
    name="record_agent",
    model=model,
    instructions=RECORD_AGENT_INSTRUCTION,
    tools=[get_schema_tool, current_time, create_records_tool, retrieve_records_tool, delete_record_tool, update_record_tool],
    model_settings=ModelSettings(parallel_tool_calls=True)
)

analysis_agent = Agent[UserContext](
    name="analysis_agent",
    model=model,
    instructions=ANALYSIS_AGENT_INSTRUCTION,
    tools=[current_time, get_schema_tool, filter_records_tool, plot_records_tool],
    model_settings=ModelSettings(parallel_tool_calls=True)
)

research_agent = Agent[UserContext](
    name="research_agent",
    model=model,
    instructions=RESEARCH_AGENT_INSTRUCTION,
    tools=[current_time, research_tool],
    model_settings=ModelSettings(parallel_tool_calls=True)
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=NAVIGATOR_AGENT_INSTRUCTION,
    handoffs=[schema_agent, record_agent, analysis_agent, research_agent],
    tools=[current_time, get_schema_tool, get_user_profile_tool],
    handoff_description="""
Pass the request for exactly agents following:
    -   schema_agent: All actions related to tables, schemas,...
    -   record_agent: All actions related to data of exsisting schemas
    -   analysis_agent: Analysing data based on user input
    -   research_agent: Resolve and find out solution for user request based on user information.
    
    Pass the request to sub-agent will full controls. 
    Do NOT call sub-agents' tools from navigator_agent, you MUST pass the request to sub-agent, and the tool is called by the sub-agents
    """,
    model_settings=ModelSettings(parallel_tool_calls=True, temperature=0.6)
    
)
