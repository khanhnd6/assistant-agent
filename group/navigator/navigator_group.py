from group.analysis.analysis_group import analysis_agent
from group.schema.schema_group import schema_agent
from group.record.record_group import record_agent
from group.navigator.navigator_tool import *
from agents import Agent, ModelSettings
from utils.hook import DebugAgentHooks
from utils.context import UserContext
from group.model import model

greeting_agent = Agent[UserContext](
    name="greeting_agent",
    model=model,
    instructions=dynamic_greeting_agent_instruction,
    hooks=DebugAgentHooks("Greeting Agent"),
    model_settings=ModelSettings(temperature=0.7)
)

navigator_agent = Agent[UserContext](
    name="navigator_agent",
    model=model,
    instructions=dynamic_navigator_agent_instruction,
    handoffs=[schema_agent, analysis_agent, greeting_agent, record_agent],
    hooks=DebugAgentHooks("Navigator Agent"),
    model_settings=ModelSettings(temperature=0, tool_choice="required")
)

gatekeeper_agent = Agent[UserContext](
    name="gatekeeper_agent",
    model=model,
    instructions=dyanmic_gatekeeper_agent_instruction,
    handoffs=[navigator_agent],
    tools=[update_profile_tool],
    hooks=DebugAgentHooks("Gatekeeper Agent"),
    model_settings=ModelSettings(temperature=0, tool_choice="required")
)