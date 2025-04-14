from agents import RunContextWrapper, FunctionTool, function_tool
from utils.context import UserContext, UserProfile
from utils.date import convert_date
import pytz

from utils.database import MongoDBConnection

@function_tool
def get_user_profile_from_context_tool(wrapper: RunContextWrapper[UserContext]) -> str:
    connection = MongoDBConnection()
    
    user_profile_data = wrapper.context.user_profile
    
    if user_profile_data:
        return str(user_profile_data)
    return "Not found current user data"
    

async def save_user_profile(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = UserProfile.model_validate_json(args)
        parsed_obj = parsed.model_dump()
        
        parsed_obj = convert_date(parsed_obj)

        timezone = parsed_obj.get("timezone", "")
        if timezone:
            if timezone not in pytz.all_timezones:
                return f"❗ Invalid timezone: '{timezone}' — must be a valid IANA timezone name (e.g., 'Asia/Ho_Chi_Minh')."

        user_id = wrapper.context.user_id
        
        parsed_obj["user_id"] = user_id
        
        connection = MongoDBConnection()
        db = connection.get_database()
        collection = db["USER_PROFILES"]
        
        result = collection.update_one({"user_id": user_id}, {"$set": parsed_obj})
        
        if result.matched_count == 0:
            collection.insert_one(parsed_obj)
            
        connection.close_connection()
        return "Successfully updated"
        
    except Exception as e:
        return f"Error happened - {str(e)}"

save_user_profile_tool = FunctionTool(
    name="save_user_profile_tool",
    description="""
        This is the tool to update user profile, it takes in an parameter as a JSON formatted string like this:
        {
            "user_name": "User name",
            "dob": "Date of birth in ISO formatted string",
            "interests": "list of string for interests",
            "region": "Current user's region in string",
            "styles": "list of strings for user styles",
            "timezone": "User location timezone",
            "instructions": "list of string for Instructions for personal direction",
        }
        
    """,
    params_json_schema=UserProfile.model_json_schema(),
    on_invoke_tool=save_user_profile
)