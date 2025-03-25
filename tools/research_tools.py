from agents import WebSearchTool
from openai.types.responses.web_search_tool_param import UserLocation

research_tool = WebSearchTool(
    search_context_size='low',
    user_location=UserLocation({
        "type": "approximate",
        "city": "Hà Nội",
        "country": "VN",
        "region": "Hà Nội",
        "timezone": "Asia/Ho_Chi_Minh"
    })
)
