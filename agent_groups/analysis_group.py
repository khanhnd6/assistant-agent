from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents import Agent, WebSearchTool, ModelSettings
from agent_groups.analysis_tool import *
from utils.hook import DebugAgentHooks
from utils.context import UserContext
from pydantic import BaseModel

model="gpt-4o-mini"

research_agent = Agent[UserContext](
    name="research_agent",
    model=model,
    handoff_description="An agent that can search for real-time data, info through Internet",
    instructions=dynamic_research_instruction_v2,
    # tools=[WebSearchTool(search_context_size="low")],
    tools=[tavily_websearch],
    hooks=DebugAgentHooks(display_name="Research Agent"),
    model_settings=ModelSettings(tool_choice="tavily_websearch")
)

class PlotOuput(BaseModel):
    success: bool

plot_agent = Agent[UserContext](
    name="plot_agent",
    handoff_description="An agent that can draw plot data",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        Follow these step:
        1. Choose the appropriate chart type automatically:
           - Use "line" chart if the x axis represents a continuous sequence (e.g., time, dates, or ordered numbers) and the y values are numerical.
           - Use "bar" chart if the x axis represents discrete categories (e.g., product names, countries) and y values are numerical.
           - Use "pie" chart only if:
            + The x values represent distinct labels/categories,
            + The y values are positive and represent parts of a whole (e.g., percentages, totals),
            + The number of data points is small (typically ≤ 6),
            + And the total sum of y is meaningful to compare as a whole (e.g., budget, proportions).
           - Avoid using "pie" chart if the y values are very close to each other or if there are too many slices.
           - If no chart type fits the data, prefer "bar" as the fallback.
        2. Prepare the data carefully accroding to `plot_records_tool` input format.
        3. Make sure to verify and preserve the correct numerical scale — e.g., don't confuse 80,000 with 8,000,000.
        4. Respect currency and number formatting based on user's language.
        5. Call `plot_records_tool` until get success response.
    """,
    tools=[plot_records_tool],
    hooks=DebugAgentHooks(display_name="Plot Agent"),
    output_type=PlotOuput,
    model_settings=ModelSettings(tool_choice="plot_records_tool")
)

plot_agent.tool_use_behavior="stop_on_first_tool"

aggregation_agent = Agent[UserContext](
    name="aggregation_agent",
    handoff_description="An agent that can do querying, analyzing, summarizing, visualizing data of user",
    instructions=dynamic_aggregation_instruction,
    tools=[
        get_all_data, 
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
        If the question is asking about user's habit (like Zodiac,.. ) hand off to research agent.
        If the question mention about "user's information" (etc: compare my paying with..), hand off to aggregation_agent.
        """,
    handoffs=[research_agent, aggregation_agent],
    hooks=DebugAgentHooks(display_name="Analysis Agent"),
    model_settings=ModelSettings(tool_choice="required")
)