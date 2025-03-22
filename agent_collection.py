from tools.schema_tools import create_schema_tool, update_schema_tool, delete_schema_tool
from tools.record_tools import create_records_tool, get_schema_tool
from tools.research_tools import research_tool
from agents import Agent, ModelSettings
from utils.context import UserContext
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
    tools=[get_schema_tool, create_records_tool],
    model_settings=ModelSettings(parallel_tool_calls=True)
)

analysis_agent = Agent[UserContext](
    name="analysis_agent",
    model=model,
    instructions=ANALYSIS_AGENT_INSTRUCTION,
)

research_agent = Agent[UserContext](
    name="research_agent",
    model=model,
    instructions=RESEARCH_AGENT_INSTRUCTION,
    tools=[research_tool],
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    handoff_description="Based on user request and information received from previous agent, find suitable handoffs to deal",
    instructions=NAVIGATOR_AGENT_INSTRUCTION,
    handoffs=[schema_agent, record_agent, analysis_agent, research_agent],
)

# research_agent.handoffs.append(navigator_agent)