import os
from agent import chat
from telegram import Update
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Application, filters

# Load biến môi trường
load_dotenv()

user = None

# Hàm xử lí các tin nhắn của chatbot
async def handle_message(update: Update, context: CallbackContext):
    global user
    if user == None:
        raw = update.message.from_user
        user = {}
        user['id'] = raw.id
        user['first_name'] = raw.first_name
        user['last_name'] = raw.last_name
    message = update.message.text
    response = await chat(message, user)
    await update.message.reply_text(str(response))


if __name__ == "__main__":
    # Tạo cổng lắng nghe tin nhắn gửi đến chatbot
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("Đang chạy chatbot..")
    app.run_polling()