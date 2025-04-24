from agents import Agent, RunContextWrapper, function_tool, FunctionTool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from utils.data_extensions import remove_first_underscore
from utils.date import convert_to_local_timezone
from group.context_tool import retrieve_schemas
from group.analysis.analysis_context import *
from utils.database import MongoDBConnection
from utils.context import UserContext
from typing import List, Dict, Any
import matplotlib.pyplot as plt
from tavily import TavilyClient
from dotenv import load_dotenv
from datetime import datetime
import ujson as json
import pytz
import os

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

@function_tool
async def tavily_websearch(
    wrapper: RunContextWrapper[UserContext], query: str
) -> List[Dict[str, Any]]:
    try:
        search_input = WebSearchInput(query=query.strip())

        client = TavilyClient(api_key=TAVILY_API_KEY)

        response = client.search(
            query=search_input.query,
            search_depth="advanced",
            max_results=5,
            include_answer=False,
            include_raw_content=False
        )

        # Parse and structure results
        results = response.get("results", [])
        formatted_results = [
            SearchResult(
                title=result.get("title", "No title"),
                url=result.get("url", "No URL"),
                content=result.get("content", "No content")
            ).dict()
            for result in results
        ]

        print(f"Retrieved {len(formatted_results)} results for query: {search_input.query}")
        return formatted_results

    except ValueError as ve:
        print(f"Validation error: {str(ve)}")
        return [{"error": f"Invalid query: {str(ve)}"}]
    except Exception as e:
        print(f"Tavily search failed: {str(e)}")
        return [{"error": f"Search error: {str(e)}"}]
    
async def plot_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = PlotArgs.model_validate_json(args)
        parsed_dict = parsed.model_dump()
        print(parsed_dict)
        parsed_dict["records"] = json.loads(parsed_dict["records"])
        chart_type = parsed_dict["chart_type"]
        x = parsed_dict["x"]
        y = parsed_dict["y"]
        data = parsed_dict["records"]
        x_vals = [d[x] for d in data] if x else None
        y_vals = [d[y] for d in data] if y else None
        pastels = ["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF"]

        plt.figure(figsize=(8, 5))
        if chart_type == "line":
            plt.plot(x_vals, y_vals, marker='o', linestyle='-')

        elif chart_type == "bar":
            plt.bar(x_vals, y_vals, color=pastels)

        elif chart_type == "pie":
            plt.pie(y_vals, labels=x_vals, colors=pastels, autopct='%1.1f%%')

        plt.xlabel(x if x else "")
        plt.ylabel(y if y else "")
        file_name = f"{wrapper.context.user_id}_image.jpg"
        plt.savefig(file_name)
        plt.close()
        return f"Generate successfully. File name: {file_name}. Agent doesn't need to call this tool again"
    except Exception as e:
        print('Try again - Error:', e)

plot_records_tool = FunctionTool(
    name="plot_records_tool",
    description="""
    Generates various types of charts from the data provided, Based on the chart type specified.
    Please get the right data from context, never generate randomlize data!
    The function returns the file path to the generated chart image.
    """,
    params_json_schema=PlotArgs.model_json_schema(),
    on_invoke_tool=plot_records,
)

@function_tool
async def get_all_data(wrapper: RunContextWrapper[UserContext], schema_name: str) -> str:
    db = MongoDBConnection().get_database()
    records = list(db['RECORDS'].find(
        {"_schema_name": schema_name, "_deleted": False},
        {"_id": 0, "_user_id": 0, "_send_notification_at": 0, "_record_id": 0, "_deleted": 0, "_schema_name": 0}
    ))
    return remove_first_underscore(convert_to_local_timezone(records, local_tz=str(wrapper.context.user_profile["timezone"])))

def dynamic_research_instruction_v2(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    profile = wrapper.context.user_profile
    region = profile['region'] if profile else "Chưa có"
    current_date = None
    if profile:
        user_timezone = pytz.timezone(profile['timezone'])
        current_date = datetime.now(pytz.utc).astimezone(user_timezone).strftime("%Y%m%d%H%M")
    instructions = [
    "Làm theo các bước sau:",
    f"1. Đừng để tâm các phần trả lời trước đó (chỉ khi nào bạn bị gọi bởi analysis_agent mới cần quan sát)",
    f"2. BẮT BUỘC tìm bằng Google để tra thông tin. Hiện tại là năm: {current_date[:4]}, tháng: {current_date[4:6]}, ngày: {current_date[6:8]}",
    f"3. Region của người dùng: {region}. Có thể cần sử dụng nếu họ hỏi những câu hỏi như sau (thời tiết ở chỗ tôi, giá vàng ở gần tôi)",
     "4. Tóm tắt kết quả trực quan, rõ ràng, có chia ý, trình bày dưới <5 câu, kèm theo nguồn đã sử dụng"
    ]   
    return '\n'.join(instructions)

def dynamic_aggregation_instruction(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    profile = wrapper.context.user_profile
    current_date = None
    if profile:
        user_timezone = pytz.timezone(profile['timezone'])
        current_date = datetime.now(pytz.utc).astimezone(user_timezone).strftime("%Y%m%d%H%M")
    instructions=[RECOMMENDED_PROMPT_PREFIX,
        "When you are transferred, do not refuse the task. Follow these step one time:",
        f"1. It is {current_date[8:]}, Day: {current_date[6:8]}, Month: {current_date[4:6]}, Year {current_date[:4]} now",
        f"2. This is all schema of users {retrieve_schemas(wrapper)}, identify the schema name that best matches the user request",
        "3. Pass the schema name to `get_all_data` tool to get all records",
        "4. If need information from external data or real-time searching, call `search_tool`",
        "5. Automatically convert all of currency data used in user's language",
        "6. Analysing by yourself",
        "7. If need to visualize data/draw plot, call `plot_tool` with all information you got. Just announce that you are plot successfully or not",
        "8. Response with the same language as users."]
    return '\n'.join(instructions)

