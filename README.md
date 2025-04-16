# Giới thiệu:

- agent_collection.py: danh sách các Agent (schema_agent, navigator_agent)
- app.py: nơi kích hoạt chatbot Telegram
- chat.py: nơi kích hoạt cuộc trò chuyện với chatbot, nạp sẵn schema trước khi trò chuyện
- context.py: định nghĩa các đối tượng dữ liệu để chatbot truyền đúng format dữ liệu vào công cụ
- database.py: tạo kết nối với mongoDB
- instructions.py: tập lệnh các yêu cầu với từng agent

# Mô tả các Agent:

- navigator_agent: tìm kiếm các agent con phù hợp với đầu vào
- schema_agent: làm việc với cấu trúc bảng trong CSDL (không tạo bảng)
  - có các tool: create, update, delete làm việc với Mongodb Local

# Xây dựng biến môi trường

- tạo file .env trong root
- Thêm các giá trị như trong .env.example

# Cách cài đặt: (3.11.5 nếu có thể)

```bash
    python -m venv myenv
    myenv\Scripts\activate # với Windows
    pip install -r requirements.txt # cài đặt các package
    python app.py # chạy chatbot trực tiếp trên Telegram
```

Nếu muốn xài trên Terminal

```bash
    # Vào chat.py và tắt comment lại vòng lặp While True
    python chat.py # chạy chatbot
```
