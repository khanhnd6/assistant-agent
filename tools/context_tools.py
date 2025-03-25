from agents import RunContextWrapper, function_tool
from utils.context import UserContext

@function_tool
async def get_schema_tool(wrapper: RunContextWrapper[UserContext]) -> str:
    try:
        return wrapper.context.schemas
    except Exception as e:
        return 'Error'