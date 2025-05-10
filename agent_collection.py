from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from tools.record_tools import create_record_tool, retrieve_records_tool, delete_record_tool, update_record_tool
from agent_groups.analysis_group import analysis_agent
from utils.hook import DebugAgentHooks
from tools.user_profile_tool import save_user_profile_tool, get_user_profile_from_context_tool
from agents import Agent, ModelSettings, handoff
from utils.context import UserContext, UserProfileOutput, RecordCommands, NavigationCommand
from instructions import *

model="gpt-4o-mini"

record_action_agent = Agent[UserContext](
    name="record_action_agent",
    model=model,
    instructions=dynamic_record_action_agent_instruction,
    tools=[create_record_tool, delete_record_tool, update_record_tool, retrieve_records_tool],
    model_settings=ModelSettings(parallel_tool_calls=True, temperature=0.5, tool_choice="retrieve_records_tool"),
    hooks=DebugAgentHooks("Record Action Agent"),
    reset_tool_choice=True
)

schema_agent_in_single_task_handler = Agent[UserContext](
    name="schema_agent_in_single_task_handler",
    model=model,
    instructions=dynamic_schema_agent_instruction,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
    model_settings=ModelSettings(temperature=0.3, tool_choice="required"),
    tool_use_behavior="stop_on_first_tool",
    reset_tool_choice=True,
    hooks=DebugAgentHooks("schema_agent_in_single_task_handler")
)

async def extract_final_ouput(output):
    return output.final_output 

single_task_handler = Agent[UserContext](
    name="single_task_handler",
    model=model,
    instructions=dynamic_single_task_handler_instruction,
    tools=[
        schema_agent_in_single_task_handler.as_tool(
            tool_name="schema_tool",
            tool_description="Tool to handle a schema-related task",
            custom_output_extractor=extract_final_ouput
        ),
        record_action_agent.as_tool(
            tool_name="record_tool",
            tool_description="Tool to handle a record-related task",
            custom_output_extractor=extract_final_ouput
        )],
    model_settings=ModelSettings(temperature=0.2, parallel_tool_calls=False),
    hooks=DebugAgentHooks("Single task handler")
)

single_task_handler_tool = single_task_handler.as_tool(
    tool_name="single_task_handler_tool",
    tool_description="Tool to handle single user request",
    custom_output_extractor=extract_final_ouput
)

task_coordinator = Agent[UserContext](
    name="task_coordinator",
    model=model,
    instructions=dynamic_task_coordinator_instruction,
    tools=[single_task_handler_tool],
    model_settings=ModelSettings(temperature=0.5, parallel_tool_calls=False, tool_choice="required"),
    reset_tool_choice = True,
    hooks=DebugAgentHooks("Task Coordinator Agent")
)

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

task_coordinating_tool = task_coordinator.as_tool(
    tool_name="task_coordinating_tool",
    tool_description="Tool to do all things related to management tasks",
    custom_output_extractor=extract_final_ouput
)

analysis_tool = analysis_agent.as_tool(
    tool_name="analysis_tool",
    tool_description="Tool to do actions like analyse, aggregate, search, recommend,..."
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=dynamic_navigator_agent_instruction,
    tools=[task_coordinating_tool, analysis_tool],
    model_settings= ModelSettings(temperature=0.8, parallel_tool_calls=False),
    hooks=DebugAgentHooks("Navigator Agent"),
)

pre_process_agent = Agent[UserContext](
    name="pre_process_agent",
    instructions=dynamic_pre_process_instruction,
    handoffs=[navigator_agent, greeting_agent],
    tools=[user_profile_agent.as_tool(
            tool_name="user_profile_tool",
            tool_description=USER_PROFILE_TOOL_DESCRIPTION
        )],
    model_settings=ModelSettings(temperature=0.3),
    hooks=DebugAgentHooks("Pre-process agent"),
)