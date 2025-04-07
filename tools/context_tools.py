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
    template = """
User Profile:
    Name: {user_name}
    Region: {region}
    Date of Birth: {dob_str}
    Interests: {interests_str}
    Special Instructions: {instructions_str}
    """
    try:
        user_data = wraper.context.user_profile
        dob_str = user_data["dob"] if user_data["dob"] is not None else "Not specified"
        interests_str = ", ".join(user_data["interests"]) if user_data["interests"] else "None listed"
        instructions_str = ", ".join(user_data["instructions"]) if user_data["instructions"] else "None"
        
        profile = template.format(
            user_name=user_data["user_name"],
            region=user_data["region"],
            dob_str=dob_str,
            interests_str=interests_str,
            instructions_str=instructions_str
        )
        return profile
    except Exception as e:
        return 'Error'
