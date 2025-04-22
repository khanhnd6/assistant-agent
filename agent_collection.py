from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from tools.record_tools import create_record_tool, retrieve_records_tool, delete_record_tool, update_record_tool
from agent_groups.analysis_group import analysis_agent
from utils.hook import DebugAgentHooks
from tools.user_profile_tool import save_user_profile_tool, get_user_profile_from_context_tool
from agents import Agent, ModelSettings, handoff
from utils.context import UserContext, UserProfileOutput, RecordCommands
from instructions import *

model="gpt-4o-mini-2024-07-18"

schema_agent = Agent[UserContext](
    name="schema_agent",
    model=model,
    instructions=dynamic_schema_agent_instruction,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
    hooks=DebugAgentHooks("Schema Agent"),
)

record_action_agent = Agent[UserContext](
    name="record_action_agent",
    model=model,
    instructions=dynamic_record_action_agent_instruction,
    tools=[create_record_tool, delete_record_tool, update_record_tool],
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
    model_settings=ModelSettings(parallel_tool_calls=True, tool_choice="retrieve_records_tool"),
    hooks=DebugAgentHooks("Record Agent")
)

record_agent.reset_tool_choice = True

schema_checker = Agent[UserContext](
    name="schema_checker",
    instructions=dynamic_record_schema_checker_agent_instruction,
    handoffs=[record_agent],
    hooks=DebugAgentHooks("Schema checker Agent")
)

task_coordinator = Agent[UserContext](
    name="task_coordinator",
    model=model,
    instructions=dynamic_task_coordinator_instruction,
    handoffs = [record_agent, schema_agent],
    tools=[],
    model_settings=ModelSettings(temperature=0.1, tool_choice="auto"),
    hooks=DebugAgentHooks("Task Coordinator Agent")
)


user_profile_agent = Agent[UserContext](
    name="user_profile_agent",
    model=model,
    instructions=USER_PROFILE_AGENT_INSTRUCTION,
    tools=[save_user_profile_tool, get_user_profile_from_context_tool],
    output_type=UserProfileOutput,
    hooks=DebugAgentHooks("User Profile Agent"),
    model_settings=ModelSettings(temperature=0.1)
)

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
    instructions=dynamic_pre_process_instruction,
    handoffs=[navigator_agent, greeting_agent],
    tools=[user_profile_agent.as_tool(
            tool_name="user_profile_tool",
            tool_description=USER_PROFILE_TOOL_DESCRIPTION
        )],
    model_settings=ModelSettings(temperature=0),
    hooks=DebugAgentHooks("Pre-process agent"),
)