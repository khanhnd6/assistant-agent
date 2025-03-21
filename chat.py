from agents import Runner, set_tracing_export_api_key
from agent_collection import navigator_agent
from utils.context import UserContext
from dotenv import load_dotenv
from utils.database import db
import asyncio
import os

load_dotenv()
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

context = None
chat_input = []
async def chat(message: str, user_id: str):
    global context, chat_input
    if context == None and user_id:
        records = db.user_context.find({"user_id": user_id})
        if records: 
            schemas = [record["schema"] for record in records if "schema" in record]
            context = UserContext(user_id = user_id, schemas=schemas)
            message = f"""
            Đây là thông tin các bảng của tôi: {schemas}. 
            Tôi chỉ cung cấp ngữ cảnh cho bạn, bạn không cần phải trả lời về chúng mà cần ghi nhớ chúng.
            Giờ quay lại cuộc đối thoại chính của chúng ta: {message}
            """
        else: context = UserContext(user_id=user_id)

    chat_input.append({"content": message, "role": "user"})
    result = await Runner.run(
        navigator_agent, 
        input=chat_input,
        context=context)
    chat_input = result.to_input_list()
    return result.final_output

# while True:
#     message = input("Nhập câu hỏi: ")
#     if message == "exit": break
#     response = asyncio.run(chat(message, '0001'))
#     print(response)