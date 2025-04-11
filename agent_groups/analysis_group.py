from agents import Agent, WebSearchTool, function_tool, RunContextWrapper, ModelSettings
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from tools.context_tools import get_schema_tool, get_user_profile_tool
from utils.date import current_time, convert_to_local_timezone
from tools.analysis_tools import plot_records_tool
from utils.database import MongoDBConnection
from utils.hook import DebugAgentHooks
from utils.context import UserContext

model="gpt-4o-mini"

@function_tool
async def get_all_data(wrapper: RunContextWrapper[UserContext], schema_name: str) -> str:
    db = MongoDBConnection().get_database()
    records = list(db['RECORDS'].find({"_user_id": wrapper.context.user_id, "_schema_name": schema_name},{"_id": 0}))
    return convert_to_local_timezone(records)

research_agent = Agent[UserContext](
    name="research_agent",
    model=model,
    handoff_description="An agent that can search for real-time data, info throught Internet",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        When you are transferred, do not refuse the task. Use the following routine ONLY ONE TIME:
        1. Call `get_user_profile_tool` ONE TIME to retrieve the user's region, then initialize the search query based on their language.
        2. Use the seach tool and produce a concise summary for the result. The summary must be 1 paragraph and less then 50 words.
        3. Capture the main points, write succinctly, no need to have complete sentences or good grammar.
        4. Remove any links, URL or hyperlink in your response
    """,
    tools=[WebSearchTool(search_context_size="low"), get_user_profile_tool],
    hooks=DebugAgentHooks(display_name="Research Agent"),
)

plot_agent = Agent[UserContext](
    name="plot_agent",
    handoff_description="An agent that can draw plot data",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        When you are transferred, do not refuse the task. Follow these step:
        1. Automatically choose the most appropriate chart type.
        2. Prepare the data carefully accroding to `plot_records_tool` input format.
        3. Make sure to verify and preserve the correct numerical scale — e.g., don't confuse 80,000 with 8,000,000.
        4. Respect currency and number formatting based on user's language.
        5. Call `plot_records_tool` to get the result.
    """,
    tools=[plot_records_tool],
    hooks=DebugAgentHooks(display_name="Plot Agent"),
)

aggregation_agent = Agent[UserContext](
    name="aggregation_agent",
    handoff_description="An agent that can do querying, analyzing, summarizing, visualizing data of user",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        When you are transferred, do not refuse the task. Follow these step one time:
        1. Call `current_time` with arugment is the region based on user's language to get specific time.
        2. Call `get_schema_tool` to get all schemas, then identify the schema name that best matches the user request.
        3. Pass the schema name to `get_all_data` tool to get all records.
        4. If need information from external data or real-time searching, call `search_tool`
        5. Automatically convert all of currency data used in user's language.
        6. If need to visualize data/draw plot, call `plot_tool` with all information you got
        7. Analysing by yourself then return a response in the same language as input. 
    """,
    tools=[
        get_schema_tool, get_all_data, current_time, 
        research_agent.as_tool(tool_name="search_tool", tool_description="A tool that can search for real-time data, info throught Internet"), 
        plot_agent.as_tool(tool_name="plot_tool", tool_description="A tool that can plot bar based on all of your information")],
    hooks=DebugAgentHooks(display_name="Aggretation Agent"),
)

analysis_agent = Agent[UserContext](
    name="analysis_agent",
    model=model,
    handoff_description="An agent that can do searching info or analysing data",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You never do tasks on your own, you always delegate customer's request to appropriate agent.
        Reminder: research_agent do not have possibility to access user's data, so when user's ask for their data, hand off to analysis agent
        """,
    handoffs=[research_agent, aggregation_agent],
    hooks=DebugAgentHooks(display_name="Analysis Agent"),
    model_settings=ModelSettings(tool_choice="required")
)