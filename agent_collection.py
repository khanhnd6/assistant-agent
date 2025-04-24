from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from tools.record_tools import create_record_tool, retrieve_records_tool, delete_record_tool, update_record_tool
from agent_groups.analysis_group import analysis_agent
from utils.hook import DebugAgentHooks
from tools.user_profile_tool import save_user_profile_tool, get_user_profile_from_context_tool
from agents import Agent, ModelSettings, handoff
from utils.context import UserContext, UserProfileOutput, RecordCommands, NavigationCommand
from instructions import *
from utils.context import ActionResult

model="gpt-4o-mini"

schema_agent = Agent[UserContext](
    name="schema_agent",
    model=model,
    instructions=dynamic_schema_agent_instruction,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
    model_settings=ModelSettings(temperature=0.5),
    hooks=DebugAgentHooks("Schema Agent"),
)

record_action_agent = Agent[UserContext](
    name="record_action_agent",
    model=model,
    instructions=dynamic_record_action_agent_instruction,
    tools=[create_record_tool, delete_record_tool, update_record_tool, retrieve_records_tool],
    model_settings=ModelSettings(parallel_tool_calls=True, temperature=0.2),
    hooks=DebugAgentHooks("Record Action Agent"),
)

handoff_record_action = handoff(agent=record_action_agent)
handoff_record_action.input_json_schema = RecordCommands.model_json_schema()


schema_agent_in_record_agent = Agent[UserContext](
    name="schema_agent_in_record_agent",
    model=model,
    instructions=dynamic_schema_agent_instruction,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
    model_settings=ModelSettings(temperature=0.5),
    tool_use_behavior="stop_on_first_tool",
    hooks=DebugAgentHooks("schema_agent_in_record_agent"),
    output_type=ActionResult
)

async def schema_tool_custom_output_extractor(output):
    return output.final_output 


record_agent = Agent[UserContext](
    name="record_agent",
    model=model,
    instructions=dynamic_record_agent_instruction,
    handoffs=[handoff_record_action],
    output_type=RecordCommands,
    tools=[retrieve_records_tool, schema_agent_in_record_agent.as_tool(
            tool_name="schema_tool",
            tool_description="Tool to execute schema-related request",
            custom_output_extractor=schema_tool_custom_output_extractor)],
    model_settings=ModelSettings(parallel_tool_calls=True, tool_choice="retrieve_records_tool", temperature=0.6),
    hooks=DebugAgentHooks("Record Agent")
)

record_agent.reset_tool_choice = True

task_coordinator = Agent[UserContext](
    name="task_coordinator",
    model=model,
    instructions=dynamic_task_coordinator_instruction,
    handoffs = [record_agent, schema_agent],
    tools=[],
    model_settings=ModelSettings(temperature=0),
    hooks=DebugAgentHooks("Task Coordinator Agent")
)
task_coordinator_handoff = handoff(agent=task_coordinator)
task_coordinator_handoff.input_json_schema = NavigationCommand.model_json_schema()

user_profile_agent = Agent[UserContext](
    name="user_profile_agent",
    model=model,
    instructions=USER_PROFILE_AGENT_INSTRUCTION,
    tools=[save_user_profile_tool, get_user_profile_from_context_tool],
    output_type=UserProfileOutput,
    hooks=DebugAgentHooks("User Profile Agent"),
    model_settings=ModelSettings(temperature=1)
)

greeting_agent = Agent[UserContext](
    name="greeting_agent",
    model=model,
    instructions=dynamic_greeting_agent_instruction,
    hooks=DebugAgentHooks("Greeting Agent"),
)

greeting_agent_handoff = handoff(agent=greeting_agent)
greeting_agent_handoff.input_json_schema = NavigationCommand.model_json_schema()

analysis_agent_handoff = handoff(agent=analysis_agent)
analysis_agent_handoff.input_json_schema = NavigationCommand.model_json_schema()

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=dynamic_navigator_agent_instruction,
    handoffs=[task_coordinator_handoff, analysis_agent_handoff],
    output_type=NavigationCommand,
    hooks=DebugAgentHooks("Navigator Agent"),
    model_settings= ModelSettings(temperature=0)
)

navigator_agent_handoff = handoff(agent=navigator_agent)
navigator_agent_handoff.input_json_schema = NavigationCommand.model_json_schema()

pre_process_agent = Agent[UserContext](
    name="pre_process_agent",
    instructions=dynamic_pre_process_instruction,
    handoffs=[navigator_agent_handoff, greeting_agent_handoff],
    output_type=NavigationCommand,
    tools=[user_profile_agent.as_tool(
            tool_name="user_profile_tool",
            tool_description=USER_PROFILE_TOOL_DESCRIPTION
        )],
    model_settings=ModelSettings(temperature=0.2),
    hooks=DebugAgentHooks("Pre-process agent"),
)