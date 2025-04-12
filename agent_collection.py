from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from tools.analysis_tools import filter_records_tool, plot_records_tool, retrieve_sample_tool
from tools.record_tools import create_records_tool, retrieve_records_tool, delete_record_tool, update_record_tool
from tools.context_tools import get_schema_tool
from agent_groups.analysis_group import analysis_agent
from tools.research_tools import research_tool
from utils.hook import DebugAgentHooks
from tools.user_profile_tool import save_user_profile_tool, get_user_profile_from_context_tool
from agents import Agent, ModelSettings, handoff
from utils.context import UserContext, UserProfileOutput, RecordCommands
from utils.date import current_time
from instructions import *
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

model="gpt-4o-mini"

schema_agent = Agent[UserContext](
    name="schema_agent",
    model=model,
    instructions=SCHEMA_AGENT_INSTRUCTION,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
    hooks=DebugAgentHooks("Schema Agent"),
)

record_action_agent = Agent[UserContext](
    name="record_action_agent",
    model=model,
    instructions=dynamic_record_action_agent_instruction,
    tools=[create_records_tool, delete_record_tool, update_record_tool],
    model_settings=ModelSettings(parallel_tool_calls=True, temperature=0.2),
    hooks=DebugAgentHooks("Record Action Agent"),
)

handoff_record_action = handoff(agent=record_action_agent)
handoff_record_action.input_json_schema = RecordCommands.model_json_schema()

record_agent = Agent[UserContext](
    name="record_agent",
    model=model,
    instructions=dynamic_record_agent_instruction,
    handoffs=[handoff_record_action],
    output_type=RecordCommands,
    tools=[retrieve_records_tool],
    model_settings=ModelSettings(parallel_tool_calls=True, tool_choice="required"),
    hooks=DebugAgentHooks("Record Agent"),
)

task_coordinator = Agent[UserContext](
    name="task_coordinator",
    model=model,
    instructions=dynamic_task_coordinator_instruction,
    handoffs = [record_agent, schema_agent],
    tools=[],
    model_settings=ModelSettings(temperature=0.5, tool_choice=None),
    hooks=DebugAgentHooks("Task Coordinator Agent")
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
    tools=[save_user_profile_tool, get_user_profile_from_context_tool],
    output_type=UserProfileOutput,
    hooks=DebugAgentHooks("User Profile Agent"),
    model_settings=ModelSettings(temperature=0.1)
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
    instructions=dynamic_greeting_agent_instruction,
    hooks=DebugAgentHooks("Greeting Agent"),
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=dynamic_navigator_agent_instruction,
    handoffs=[task_coordinator, analysis_agent],
    hooks=DebugAgentHooks("Navigator Agent"),
    model_settings= ModelSettings(tool_choice="required", temperature=0.5)
)



pre_process_agent = Agent[UserContext](
    name="pre_process_agent",
    instructions=f"""
    {RECOMMENDED_PROMPT_PREFIX}
    You are helpful agent to navigate task and save user information
    
    Handoff rules:
    - `greeting_agent`: just greeting
    - `navigator_agent`: handle with other like actions, tasks, data structures, analysing, researching and so on.
    
    Tool usage: 
    - `user_profile_tool`: to save personal information like: user name, date of birth, region, styles, interests and instructions only
    
    If both tool and handoff task are needed to call, call tool first, receive a response and handoff the request to possible agent
    
    """,
    handoffs=[navigator_agent, greeting_agent],
    tools=[user_profile_agent.as_tool(
            tool_name="user_profile_tool",
            tool_description="""
Tool to save user information including: 
- user name
- date of birth
- region
- styles
- interests
- instructions: The rules for agents

Other information is skip
            """
        )],
    model_settings=ModelSettings(tool_choice="required", temperature=0),
    hooks=DebugAgentHooks("Pre-process agent")
)