from agents import RunContextWrapper, function_tool
from utils.context import UserContext
import pytz
from tzlocal import get_localzone
from datetime import datetime


USER_PROFILE_TEMPLATE = """
User Profile:
    Name: {user_name}
    Region: {region}
    Date of Birth: {dob_str}
    Interests: {interests_str}
    Special Instructions: {instructions_str}
    """

@function_tool
async def get_schema_tool(wrapper: RunContextWrapper[UserContext]) -> str:
    try:
        return wrapper.context.schemas
    except Exception as e:
        return 'Error'

@function_tool
async def get_user_profile_tool(wrapper: RunContextWrapper[UserContext]) -> str:
    try:
        user_data = wrapper.context.user_profile
        dob_str = user_data["dob"] if user_data["dob"] is not None else "Not specified"
        interests_str = ", ".join(user_data["interests"]) if user_data["interests"] else "None listed"
        instructions_str = ", ".join(user_data["instructions"]) if user_data["instructions"] else "None"
        
        profile = USER_PROFILE_TEMPLATE.format(
            user_name=user_data["user_name"],
            region=user_data["region"],
            dob_str=dob_str,
            interests_str=interests_str,
            instructions_str=instructions_str
        )
        return profile
    except Exception as e:
        return 'Error'



@function_tool
async def get_context_tool(wrapper: RunContextWrapper[UserContext]) -> dict:
    try:
        
        print(wrapper.context)
        
        schemas = wrapper.context.schemas if wrapper.context and wrapper.context.schemas else []

        user_data = wrapper.context.user_profile

        dob_str = user_data.get("dob") or "Not specified"
        
        interests = user_data.get("interests") or []
        interests_str = ", ".join(interests) if isinstance(interests, list) else str(interests)

        instructions = user_data.get("instructions") or []
        instructions_str = ", ".join(instructions) if isinstance(instructions, list) else str(instructions)

        user_profile = USER_PROFILE_TEMPLATE.format(
            user_name=user_data.get("user_name", "Unknown"),
            region=user_data.get("region", "Unknown"),
            dob_str=dob_str,
            interests_str=interests_str,
            instructions_str=instructions_str
        )

        local_tz = get_localzone()
        utc_tz = pytz.UTC
        now = datetime.now(utc_tz).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S %z")

        return {
            "schemas": schemas,
            "user_profile": user_profile,
            "current_time": now
        }
    except Exception as e:
        return {"error": f"Error happened - {str(e)}"}

@function_tool
async def get_context_tool(wrapper: RunContextWrapper[UserContext]) -> dict:
    """
    Retrieves the user's schemas and raw profile data from the context.
    
    Returns:
        dict: {
            "schemas": list[dict],  # List of schema dictionaries
            "user_profile": dict,   # Raw user profile data
            "error": str            # Present only if an error occurs
        }
    """
    try:
        # Fetch schemas (list of schema dicts)
        schemas = wrapper.context.schemas
        
        # Fetch raw user profile (dict)
        user_profile = wrapper.context.user_profile
        
        # Return combined result
        return {
            "schemas": schemas,
            "user_profile": user_profile
        }
    except Exception as e:
        return {"error": f"Error retrieving context: {str(e)}"}
