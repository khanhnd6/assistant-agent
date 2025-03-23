from agents import Runner, set_tracing_export_api_key
from utils.database import MongoDBConnection
from agent_collection import navigator_agent
from utils.context import UserContext
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

context = None
chat_input = []
async def chat(message: str, user_id: str):
    global context, chat_input
    if context == None and user_id:
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        db_schemas = db["SCHEMAS"].find({"user_id": user_id})
        # db_user_profile = db["USER_PROFILES"].find({"user_id": user_id})
        
        mongodb_connection.close_connection()
        
        if db_schemas: 
            schemas = [record for record in db_schemas]
            # user_information = db_user_profile[0]
            user_information = ''
            context = UserContext(user_id = user_id, schemas=schemas)
            message = f"""Your Context:
            1. User information:
            {user_information}
            
            2. Table schemas with structure 
            {schemas}
            
            You have to refer to user information and schemas in the context to personalize the response and use it as the context
            Proceed with main user's request: {message}.
            """
        else: context = UserContext(user_id=user_id)

    chat_input.append({"content": message, "role": "user"})
    result = await Runner.run(
        navigator_agent, 
        input=chat_input,
        context=context)
    chat_input = chat_input + [result.to_input_list()[-1]]
    return result.final_output

while True:
    message = input("Nhập tin nhắn: ")
    if message == "q": 
        os.system("cls")
        break
    response = asyncio.run(chat(message, 'khanh'))
    print(response)