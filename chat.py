from agents import Runner, RunConfig, set_tracing_export_api_key
from utils.database import MongoDBConnection, RedisCache
from agent_collection import pre_process_agent
from utils.context import UserContext
from dotenv import load_dotenv
import ujson as json
import os
import time
import re
load_dotenv()
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

REDIS_EXPERATION_IN = 1800 # 30 mins
r = RedisCache()

def clean_for_telegram(text):
    # Thay ký tự theo yêu cầu
    text = re.sub(r'^(?!.*\*.*\*).*?\*', lambda m: m.group(0).replace('*', '-'), text, flags=re.M)
    return text

async def chat(message: str, user_id: int, is_sys_message = False):

    try:
        start_time = time.time()
        conversation = []
        context = None
        # if user_id:
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        db_schemas = db["SCHEMAS"].find({"user_id": user_id, "deleted": False}, {"_id": 0})
        db_user_profile = db["USER_PROFILES"].find_one({"user_id": user_id}, {"_id": 0})
        
        context = UserContext(user_id = user_id, schemas=[schema for schema in db_schemas], user_profile=db_user_profile)
        mongodb_connection.close_connection()
        
        # retrieve chat history
        start_time = time.time()
        chat_history = r.get(f"chat-history:{user_id}")
        if chat_history:
            chat_history_str = chat_history.decode('utf-8') if isinstance(chat_history, bytes) else chat_history
            conversation = json.loads(chat_history_str)
        print("Redis:", time.time() - start_time)
        
        conversation.append({"content": message, "role": "system" if is_sys_message else "user"})
        start_time = time.time()
        result = await Runner.run(
            pre_process_agent, 
            input=conversation,
            context=context,
            run_config=RunConfig(workflow_name="TEST")
            )
        if isinstance(result.final_output, str):
            conversation = conversation + [result.to_input_list()[-1]]
            conversation = conversation[-10:]
            print("LLM:",time.time() - start_time)
            r.set(f"chat-history:{user_id}", json.dumps(conversation), REDIS_EXPERATION_IN)
            return clean_for_telegram(result.final_output)
        return result.final_output
    except Exception as ex:
        print(f"Error in chat: {str(ex)}")
        return "Error happened, please try again!"


