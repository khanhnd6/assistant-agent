from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
# from tools.analysis_tools import filter_records_tool, plot_records_tool, retrieve_sample_tool
from tools.record_tools import create_records_tool, retrieve_records_tool, delete_record_tool, update_record_tool
from tools.context_tools import get_schema_tool, get_user_profile_tool, get_context_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from tools.research_tools import research_tool
from tools.user_profile_tool import save_user_profile_tool, get_db_user_profile_tool
from agents import Agent, ModelSettings
from utils.context import UserContext
from utils.hook import DebugAgentHooks
from utils.date import current_time
from instructions import *
from agent_groups.analysis_group import analysis_agent

model="gpt-4o-mini"

schema_agent = Agent[UserContext](
    name="schema_agent",
    model=model,
    instructions=SCHEMA_AGENT_INSTRUCTION,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
    hooks=DebugAgentHooks("Schema Agent")
)

record_agent = Agent[UserContext](
    name="record_agent",
    model=model,
    instructions=RECORD_AGENT_INSTRUCTION,
    tools=[get_schema_tool, current_time, create_records_tool, retrieve_records_tool, delete_record_tool, update_record_tool],
    model_settings=ModelSettings(parallel_tool_calls=True),
    hooks=DebugAgentHooks("Record Agent")
)

# analysis_agent = Agent[UserContext](
#     name="analysis_agent",
#     model=model,
#     instructions=ANALYSIS_AGENT_INSTRUCTION,
#     tools=[current_time, get_schema_tool, filter_records_tool, plot_records_tool, research_tool, retrieve_sample_tool],
#     model_settings=ModelSettings(parallel_tool_calls=True),
#     hooks=DebugAgentHooks("Analysis Agent")
# )

# research_agent = Agent[UserContext](
#     name="research_agent",
#     model=model,
#     instructions=RESEARCH_AGENT_INSTRUCTION,
#     tools=[current_time, research_tool],
#     model_settings=ModelSettings(parallel_tool_calls=True),
#     hooks=DebugAgentHooks("Research Agent")
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
#     handoffs=[schema_agent, record_agent, analysis_agent],
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
#         Do NOT call sub-agent tools. Delegate only.
#     """,
#     hooks=DebugAgentHooks("Navigator Agent")
# )

greeting_agent = Agent[UserContext](
    name="greeting_agent",
    model=model,
    hooks=DebugAgentHooks("Greeting Agent"),
    tools=[
        current_time,
        user_profile_agent.as_tool(
            tool_name="user_profile", 
            description="A tool that manages, organize and update personal information.")
    ]
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=
    f"""{RECOMMENDED_PROMPT_PREFIX}
        You are helpful navigator agent. Based on user's question, you must handoff to other appropriate agents.
        - greeting_agent: Use this agent when the user wants to greeeting or calibration tasks.

        - schema_agent: Use this agent when the user wants to **define, create, or modify schemas or data structures**, \
          such as creating a new type of data to store (e.g., "I want to save paying data", "Add a field for location").

        - record_agent: Use this agent when the user wants to **add, update, or delete individual records** based on an \
          existing schema. This includes **inputting new data**, modifying values, or deleting entries. (e.g., "I paid $10 \
          today", "Update the amount of this record", "Delete the record from last week").

        - analysis_agent:  Focuses on **querying, analyzing, summarizing, visualizing data, or researching info & facts**. Use this agent \
          when the user wants to extract insights, explore trends, apply filters, or ask higher-level questions involving the data. \
          (e.g., “How much have I spent between A and B?”, “Show me all expenses in March”, “Plot a bar chart of spending by category”, 
          “What category do I spend most on?”, “Find unusual trends in my data”.)

        Decision rule:
        - If the user is **defining or changing the structure** of data → schema_agent  
        - If the user is **inputting, modifying, or removing records** → record_agent  
        - If the user is **exploring, analyzing, summarizing, or researching data** → analysis_agent
    """,
    handoffs=[schema_agent, record_agent, analysis_agent, greeting_agent],
    hooks=DebugAgentHooks("Navigator Agent"),
    model_settings= ModelSettings(tool_choice="required")
)
