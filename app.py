from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Application, filters
from dotenv import load_dotenv
from telegram import Update
from chat import chat
import os

# Load biến môi trường
load_dotenv()

user_id = None

# Hàm xử lí các tin nhắn của chatbot
async def handle_message(update: Update, context: CallbackContext):
    global user_id
    if user_id == None:
        user_id = update.message.from_user.id
    message = update.message.text
    response = await chat(message, user_id)
    await update.message.reply_text(str(response), parse_mode='markdown')

    photo_path = "image.jpg"
    if os.path.exists(photo_path):  
        with open(photo_path, "rb") as photo:
            await update.message.reply_photo(photo=photo)
        os.remove(photo_path)

if __name__ == "__main__":
    # Tạo cổng lắng nghe tin nhắn gửi đến chatbot
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("Đang chạy chatbot @assistant_tlu_bot..")
    app.run_polling()