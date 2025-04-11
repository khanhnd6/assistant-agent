from agents import RunContextWrapper, function_tool
from utils.context import UserContext
# import pytz
# from tzlocal import get_localzone
# from datetime import datetime


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
        return f'Error: {e}'



# @function_tool
def get_context_tool(wrapper: UserContext) -> dict:
    try:
        # print(wrapper)

        schemas = getattr(wrapper, 'schemas', []) or []

        user_data = getattr(wrapper, 'user_profile', {}) or {}

        dob_str = user_data.get("dob") or "Not specified"

        interests = user_data.get("interests")
        if isinstance(interests, list):
            interests_str = ", ".join(interests)
        elif interests:
            interests_str = str(interests)
        else:
            interests_str = "No interests specified"

        instructions = user_data.get("instructions")
        if isinstance(instructions, list):
            instructions_str = ", ".join(instructions)
        elif instructions:
            instructions_str = str(instructions)
        else:
            instructions_str = "No instructions specified"

        user_profile = USER_PROFILE_TEMPLATE.format(
            user_name=user_data.get("user_name", "Unknown"),
            region=user_data.get("region", "Unknown"),
            dob_str=dob_str,
            interests_str=interests_str,
            instructions_str=instructions_str
        )

        # local_tz = get_localzone()
        # now = datetime.now(pytz.UTC).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S %z")

        return {
            "schemas": schemas if len(schemas) > 0 else "Not existed schemas",
            "user_profile": user_profile,
            # "current_time": now
        }

    except Exception as e:
        return {"error": f"Error happened - {e}"}
