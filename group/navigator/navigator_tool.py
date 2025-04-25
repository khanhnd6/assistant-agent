from group.context_tool import retrieve_user_profile, retrieve_display_schemas
from group.navigator.navigator_context import UpdateProfile
from agents import Agent, RunContextWrapper, FunctionTool
from utils.date import convert_date, current_time_v3
from utils.database import MongoDBConnection
from utils.context import UserContext
from group.prompt import *
import pytz

async def dynamic_greeting_agent_instruction(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
  profile = wrapper.context.user_profile
  current = current_time_v3(profile["timezone"]) if profile else current_time_v3()
  instruction = f"""
    {STANDALONE_PREFIX_PROMPT}
    Your mission is to warmly greet the user and spark interactive, delightful conversations
    - Modify the response to be more polite and natural, without directly referencing the user's interests 100% of the time: {retrieve_user_profile(wrapper)}
    - Include emoji or a touch of humor in your response.
    - After greeting, always invite the user to take an action, ask a question, or explore a feature.
    - Here is also current time for you: {current}
  """
  return instruction

async def dynamic_navigator_agent_instruction(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
  instruction = f"""
    {HANDOFFABLE_PREFIX_PROMPT}
    Delegate tasks by hand off to just ONE appropiate agent.:
    - analysis_agent: analyze, aggreagate, summerize, research data. Ask for real-time information
      Example: "How much did I spend this month", "Compare my expenses between..", "How is the weather today?", "What's news today?", "Toàn bộ lịch trình của tôi",..
    - schema_agent: initialize a new data schema for saving and structuring user records. Never call this for making user profile schema.
      Examples: “I want to take notes”, “I'm ready to set up a planner”, "create table for planning",..
    - greeting_agent: andles casual greetings, small talks, talk about dob, region, favorite things, styles,...
      Examples: “Good morning!”, “How are you?”, "Hello", "What time is this,.."
    - record_agent: CRUD user's records and information that have been saved.
      Examples: "I want to note..", "Save my plan..",..
  """
  return instruction

async def dyanmic_gatekeeper_agent_instruction(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
  profile = wrapper.context.user_profile
  timezone = "Có rồi" if profile else "Chưa"
  instruction = f"""
    {HANDOFFABLE_PREFIX_PROMPT}
    Bạn có trách nhiệm kiểm tra xem tin nhắn của người dùng có nhắc đến thông tin cá nhân của họ không?
    Bao gồm: tên, ngày sinh, region, múi giờ, sở thích, phong cách hoặc chỉ dẫn riêng của bản thân
    VD: Tôi sinh ngày,... Tôi có sở thích là,.... Địa chỉ của tôi ở Hà Nội..., Tôi thích cái này., Tôi sinh ra ở Hà Nội,...
    1. Nếu gặp những câu như trên, lập tức thực hiện các công việc dưới đây mà không nói với người dùng
    - So sánh thông tin sắp thay đổi với danh sách thông tin cũ: {retrieve_user_profile(wrapper)}
    - Chọn ra những trường/thông tin cần cập nhật, rồi chuẩn bị đầu vào theo yêu cầu của hàm `update_profile_tool` rồi gọi nó để được cập nhật
    - Họ có timezone chưa?: {timezone}. Nếu chưa, mà họ lại cung cấp về region thì tự cập nhật cả timezone (VD: "Tôi sống ở Hà nội" -> timezone: "Asisa/Ho_Chi_Minh")
    - Nếu bạn muốn update nhiều thông tin, gọi hàm đó thêm lần nữa.
    - Cấm nhắc tới việc bạn đã lưu hay cập nhật thông tin cá nhân người dùng. Lập tức chuyển giao sang `navigator_agent` để nó trò chuyện bình thường

    2. Ngược lại, nếu họ nhắc tới: {retrieve_display_schemas(wrapper)} thì BUỘC chuyển giao ngay cho `navigator_agent`: 
  """
  return instruction

async def update_user_profile(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = UpdateProfile.model_validate_json(args)
        parsed_obj = parsed.model_dump()
        user_id = wrapper.context.user_id

        connection = MongoDBConnection()
        db = connection.get_database()
        collection = db["USER_PROFILES"]

        field = parsed_obj["name"]
        value = parsed_obj["value"]

        if field in ("user_name", "region"):
            collection.update_one({"user_id": user_id}, {"$set": {field: str(value)}})

        elif field == "timezone":
            if value not in pytz.all_timezones:
                raise ValueError(f"Invalid timezone: '{value}' — must be a valid IANA timezone name (e.g., 'Asia/Ho_Chi_Minh').")
            collection.update_one({"user_id": user_id}, {"$set": {"timezone": value}})

        elif field == "dob":
            collection.update_one({"user_id": user_id}, {"$set": {"dob": convert_date(value)}})
        else:
            doc = collection.find_one({"user_id": user_id}, {field: 1})
            if doc is None or not isinstance(doc.get(field, []), list):
                collection.update_one({"user_id": user_id}, {"$set": {field: []}})
            collection.update_one({"user_id": user_id},
                                  {"$addToSet": {field: value}})

        connection.close_connection()
        return "Successfully updated"

    except Exception as e:
        return f"Error happened - {str(e)}"

update_profile_tool = FunctionTool(
    name="update_profile_tool",
    description="""
        This is the tool to update one of user profile's field. You may want to call it again if update multiple fields.
    """,
    params_json_schema=UpdateProfile.model_json_schema(),
    on_invoke_tool=update_user_profile
)