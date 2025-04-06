from agents import Runner, set_tracing_export_api_key, set_default_openai_key
from utils.database import MongoDBConnection, RedisCache
from agent_collection import navigator_agent
from utils.context import UserContext
from dotenv import load_dotenv
import asyncio
import json
import os
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
# set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

REDIS_EXPERATION_IN = 1800 # 30 mins

async def chat(message: str, user_id: str):
    try:
        conversation = []
        context = None
        r = RedisCache()
        if user_id:
            mongodb_connection = MongoDBConnection()
            db = mongodb_connection.get_database()
            db_schemas = db["SCHEMAS"].find({"user_id": user_id})
            # db_user_profile = db["USER_PROFILES"].find({"user_id": user_id})
            mongodb_connection.close_connection()
            
            if db_schemas: 
                schemas = [record for record in db_schemas]
                context = UserContext(user_id = user_id, schemas=schemas)
            else: context = UserContext(user_id=user_id)
            
            # retrieve chat history
            chat_history = r.get(f"chat-history:{user_id}")
            if chat_history:
                chat_history_str = chat_history.decode('utf-8') if isinstance(chat_history, bytes) else chat_history
                conversation = json.loads(chat_history_str)
        
        conversation.append({"content": message, "role": "user"})
        result = await Runner.run(
            navigator_agent, 
            input=conversation,
            context=context)
        # conversation = conversation + [result.to_input_list()[-1]]
        conversation = result.to_input_list()[-80:]
        print(conversation)

        r.set(f"chat-history:{user_id}", json.dumps(conversation), REDIS_EXPERATION_IN)
        return result.final_output
    except Exception as ex:
        logger.error(f"Error in chat: {str(ex)}")
        return "Error happened, please try again!"

# while True:
#     message = input("Nhập câu hỏi: ")
#     if message == "q": 
#         os.system("cls")
#         break
#     response = asyncio.run(chat(message, 'khanh2'))
#     print(response)

