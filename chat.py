from agents import Runner, set_tracing_export_api_key
from utils.database import MongoDBConnection, RedisCache
from agent_collection import pre_process_agent
from utils.context import UserContext
from dotenv import load_dotenv
# from tools.context_tools import get_context_tool
import ujson as json
import os
import time
# import logging
# import asyncio

# import pytz
# from tzlocal import get_localzone
# from datetime import datetime

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

load_dotenv()
# set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

REDIS_EXPERATION_IN = 1800 # 30 mins
r = RedisCache()

async def chat(message: str, user_id: int):
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
            # context_obj = get_context_tool(context)

            # conversation.append({
            #     "role": "system",
            #     "content": json.dumps(context_obj)
            # })
            
        # local_tz = get_localzone()
        # now = datetime.now(pytz.UTC).astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S %z")
        
        # conversation.append({
        #     "role": "system",
        #     "content": f"Current time: {now}"
        # })
        
        conversation.append({"content": message, "role": "user"})
        start_time = time.time()
        result = await Runner.run(
            pre_process_agent, 
            input=conversation,
            context=context)
        conversation = conversation + [result.to_input_list()[-1]]
        conversation = conversation[-10:]
        print("LLM:",time.time() - start_time)
        r.set(f"chat-history:{user_id}", json.dumps(conversation), REDIS_EXPERATION_IN)
        return result.final_output
    except Exception as ex:
        # # logger.error(f"Error in chat: {str(ex)}")
        raise ex
        print(f"Error in chat: {str(ex)}")
        return "Error happened, please try again!"

# while True:
#     message = input("Nhập câu hỏi: ")
#     if message == "q": 
#         os.system("cls")
#         break
#     response = asyncio.run(chat(message, 'khanh'))
#     print(response)

