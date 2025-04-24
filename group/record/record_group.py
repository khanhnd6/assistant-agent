from tools.record_tools import retrieve_records_tool
from group.schema.schema_group import schema_agent
from group.record.record_context import RecordJob
from agents import Agent, ModelSettings
from group.record.record_tool import *
from utils.hook import DebugAgentHooks
from utils.context import UserContext
from group.model import model

action_agent = Agent[UserContext](
    name="record_action_agent",
    model=model,
    instructions=dynamic_action_agent_instruction,
    tools=[retrieve_records_tool, create_record_tool, delete_record_tool, update_record_tool],
    hooks=DebugAgentHooks("Record Action Agent"),
    model_settings=ModelSettings(tool_choice="required"),
)

schema_agent_clone = schema_agent.clone()
schema_agent_clone.model_settings = ModelSettings(tool_choice="create_schema_tool")

record_agent = Agent[UserContext](
    name="record_agent",
    model=model,
    instructions=dynamic_record_agent_instruction,
    tools=[
        schema_agent_clone.as_tool(tool_name="create_schema_tool", tool_description="Create a new data‑schema when the requested schema does not yet exist"),
        action_agent.as_tool(tool_name="action_record_tool", tool_description="A tool that can process job based on provided argument (action, existed, request, schema). You prefer to call this")
    ],
    model_settings=ModelSettings(tool_choice="required"),
    hooks=DebugAgentHooks("Record Agent")
)