from agents import RunContextWrapper, function_tool
from utils.context import UserContext

@function_tool
async def get_schema_tool(wrapper: RunContextWrapper[UserContext]) -> str:
    try:
        return wrapper.context.schemas
    except Exception as e:
        return 'Error'
    
@function_tool
async def get_user_profile_tool(wraper: RunContextWrapper[UserContext]) -> str:
    try:
        return wraper.context.user_profile
    except Exception as e:
        return 'Error'