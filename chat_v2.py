from agents import Runner, set_tracing_export_api_key, trace
from group.navigator.navigator_group import gatekeeper_agent
from utils.database import MongoDBConnection, RedisCache
from utils.context import UserContext
from dotenv import load_dotenv
import ujson as json
import os
import re

load_dotenv()
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

REDIS_EXPERATION_IN = 1800
r = RedisCache()
r.clear()
m = MongoDBConnection()
# m.wipeout()
# m.close_connection()

async def chat(message: str, user_id: int, is_sys_message = False):
    try:
        # Thiết lập ngữ cảnh
        context = None
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        db_schemas = db["SCHEMAS"].find({"user_id": user_id, "deleted": False}, {"_id": 0})
        db_user_profile = db["USER_PROFILES"].find_one({"user_id": user_id}, {"_id": 0})
        context = UserContext(user_id = user_id, schemas=[schema for schema in db_schemas], user_profile=db_user_profile)
        mongodb_connection.close_connection()
        
        # Thiết lập lịch sử trò chuyện
        conversation = []
        chat_history = r.get(f"chat-history:{user_id}")
        if chat_history:
            chat_history_str = chat_history.decode('utf-8') if isinstance(chat_history, bytes) else chat_history
            conversation = json.loads(chat_history_str)
        conversation.append({"content": message, "role": "system" if is_sys_message else "user"})

        # Tạo phản hồi và lưu lại lịch sử trò chuyện
        result = None
        with trace(workflow_name="Thử nghiệm V3:"):
            result = await Runner.run(gatekeeper_agent, input=conversation, context=context)
        conversation = conversation + [result.to_input_list()[-1]]
        conversation = conversation[-8:]
        r.set(f"chat-history:{user_id}", json.dumps(conversation), REDIS_EXPERATION_IN)
        clean_text = re.sub(r'^(?!.*\*.*\*).*?\*', lambda m: m.group(0).replace('*', '-'), result.final_output, flags=re.M)
        print(clean_text)
        return clean_text

    except Exception as ex:
        raise f"Error in chat: {str(ex)}"


