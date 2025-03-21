from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from utils.context import UserContext
from instructions import *
from agents import Agent

model="gpt-4o-mini"

schema_agent = Agent[UserContext](
    name="schema_agent",
    model=model,
    instructions=SCHEMA_AGENT_INSTRUCTION,
    tools=[create_schema_tool, update_schema_tool, delete_schema_tool]
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=NAVIGATOR_AGENT_INSTRUCTION,
    handoffs=[schema_agent],
)