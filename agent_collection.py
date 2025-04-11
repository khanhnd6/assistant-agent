from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from tools.analysis_tools import filter_records_tool, plot_records_tool, retrieve_sample_tool
from tools.record_tools import create_records_tool, retrieve_records_tool, delete_record_tool, update_record_tool
from tools.context_tools import get_schema_tool, get_user_profile_tool, get_context_tool
from agent_groups.analysis_group import analysis_agent
from tools.research_tools import research_tool
from utils.hook import DebugAgentHooks
from tools.user_profile_tool import save_user_profile_tool, get_db_user_profile_tool
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
    hooks=DebugAgentHooks("Schema Agent"),
)

record_agent = Agent[UserContext](
    name="record_agent",
    model=model,
    instructions=RECORD_AGENT_INSTRUCTION,
    tools=[get_schema_tool, current_time, create_records_tool, retrieve_records_tool, delete_record_tool, update_record_tool],
    model_settings=ModelSettings(parallel_tool_calls=True),
    hooks=DebugAgentHooks("Record Agent"),
)

# analysis_agent = Agent[UserContext](
#     name="analysis_agent",
#     model=model,
#     instructions=ANALYSIS_AGENT_INSTRUCTION,
#     tools=[current_time, get_schema_tool, filter_records_tool, plot_records_tool, research_tool, retrieve_sample_tool],
#     model_settings=ModelSettings(parallel_tool_calls=True)
# )

# research_agent = Agent[UserContext](
#     name="research_agent",
#     model=model,
#     instructions=RESEARCH_AGENT_INSTRUCTION,
#     tools=[current_time, research_tool],
#     model_settings=ModelSettings(parallel_tool_calls=True)
# )

user_profile_agent = Agent[UserContext](
    name="user_profile_agent",
    model=model,
    instructions=USER_PROFILE_AGENT_INSTRUCTION,
    tools=[save_user_profile_tool, get_db_user_profile_tool],
    hooks=DebugAgentHooks("User Profile Agent")
)

# navigator_agent = Agent[UserContext](
#     name="navigator_agent",
#     model=model,
#     instructions=NAVIGATOR_AGENT_INSTRUCTION,
#     handoffs=[schema_agent, record_agent, analysis_agent, research_agent],
#     tools=[
#         user_profile_agent.as_tool(
#             tool_name="user_profile_tool",
#             tool_description="Handle with updating the user's information."
#         ),
#     ],
#     handoff_description="""
#         Delegate the ENTIRE request to EXACTLY ONE sub-agent:
#         - schema_agent: For schema tasks.
#         - record_agent: For record tasks (including multiple records).
#         - analysis_agent: For analysis and research tasks.
#         - research_agent: searches for external information and gives suggestions
#         Do NOT call sub-agent tools. Delegate only.
#     """,    
# )

greeting_agent = Agent[UserContext](
    name="greeting_agent",
    model=model,
    hooks=DebugAgentHooks("Greeting Agent"),
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=NAVIGATOR_AGENT_INSTRUCTION_V2,
    handoffs=[schema_agent, record_agent, analysis_agent, greeting_agent, user_profile_agent],
    hooks=DebugAgentHooks("Navigator Agent"),
    model_settings= ModelSettings(tool_choice="required")
)
