from agents import Agent, RunContextWrapper, Runner, function_tool, handoff, InputGuardrail,GuardrailFunctionOutput
from pydantic import BaseModel
from db import execute_query
from agents import set_tracing_export_api_key
from dotenv import load_dotenv
import os
import asyncio
from dataclasses import dataclass

load_dotenv()
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
model = 'gpt-4o-mini'

# bao gồm name, instruction/instructions_function - chỉ thị ban đầu
# description - mô tả cho subagent, tools - danh sách công cụ
# handoffs - danh sách các subagent khác mà agent này có thể chuyển giao
# model_setting - cài đặt mô hình
# output_type - kiểu dữ liệu đầu ra (mặc định là chuỗi, có thể tự định nghĩa)
# context-Type: ngữ cảnh của agent (class Context)
# Context sử dụng khi muốn gửi session, thông tin đăng nhập người dùng

# tạo vòng lặp
# mô hình sẽ lấy đầu vào, tin nhắn hệ thống, danh sách công cụ
# có thể tạo tin nhắn cuối hoặc gọi công cụ hay subagent khác
# nếu nó gọi công cụ, kết quả sẽ trả về cuộc trò chuyện. Tiến trình tiếp tục cho tới khi nhận được message cuối cùng hoặc đi qua hết handoff
# nếu cài đặt kiểu đầu ra (Pydanic Model), agent phải gọi final_output tool để tạo ra JSON
# có thể cài đặt max_turns để giới hạn vòng lặp

@dataclass
class UserInfo:  
    id: str

@function_tool
async def execute_query_tool(query: str):
    result = execute_query(query)
    return result

retrive_agent = Agent(
    name="Math Tutor",
    handoff_description="Một trợ lý chuyên về lấy thông tin đã lưu trữ",
    instructions="""
    Bạn sẽ giúp người dùng lấy thông tin đã lưu trữ từ cơ sở dữ liệu thông qua 1 công cụ có tên là execute_query_tool.
    Nếu ban đầu, bạn không có thông tin về bảng nào trong CSDL, vui lòng viết query SQL để tra cứu thông tin toàn bộ các bảng trong CSDL. Sau đó, truyền vào execute_query_tool để lấy thông tin các bảng đó.
    Khi đã xác định được thông tin các bảng, chọn bảng phù hợp với yêu cầu người dùng hoặc tự tạo bảng mới.
    Trước hết, bạn cần phải nghĩ query SQL, sau đó mới truyền vào công cụ đó.
    Cuối cùng, về phản hồi cho người dùng, vui lòng trả về query SQL mà bạn đã viết kèm kết quả cuối cùng.
    """,
    tools=[execute_query_tool],
    model=model,
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Bạn sẽ xác định xem người dùng đang hỏi cái gì và gọi các agent khác phù hợp. Nếu người dùng hỏi về thông tin chi tiêu, bạn sẽ gọi retrive_agent",
    handoffs=[retrive_agent],
    model=model,
)

async def chat(message: str, user: dict = None):
    result = await Runner.run(
        triage_agent, 
        input=message,)
    print(result.to_input_list())
    print('----------------')
    return result.final_output

context = []
while True:
    message = input("Nhập câu hỏi: ")
    if message == "exit":
        break
    full_message = "Hội thoại trước đó: " + "\n".join(context) + "\n" + "Câu hỏi hiện tại: " + message
    response = asyncio.run(chat(full_message))
    context.append(response)
    print(response)