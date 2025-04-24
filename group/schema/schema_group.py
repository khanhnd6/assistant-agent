from agents import Agent, ModelSettings
from utils.hook import DebugAgentHooks
from group.schema.schema_tool import *
from utils.context import UserContext
from group.model import model

schema_agent = Agent[UserContext](
    name="schema_agent",
    model=model,
    instructions=dynamic_schema_agent_instruction,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool],
    hooks=DebugAgentHooks("Schema Agent"),
)