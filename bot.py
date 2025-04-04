from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Application, filters
from dotenv import load_dotenv
from telegram import Update
from chat import chat
import os
import asyncio
load_dotenv()

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message = update.message.text
    response = await chat(message, user_id)
    await update.message.reply_text(str(response), parse_mode='markdown')

    photo_path = "image.jpg"
    if os.path.exists(photo_path):  
        with open(photo_path, "rb") as photo:
            await update.message.reply_photo(photo=photo)
        os.remove(photo_path)

# if __name__ == "__main__":
#     # Tạo cổng lắng nghe tin nhắn gửi đến chatbot
#     app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
#     app.add_handler(MessageHandler(filters.TEXT, handle_message))
#     print("Đang chạy chatbot @assistant_tlu_bot..")
#     app.run_polling()
    
# async def run_bot():
#     app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
#     # Add handlers
#     app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
#     print("Telegram bot is running...")
    
#     try:
#         await app.initialize()
#         await app.start()
        
#         await app.updater.start_polling(drop_pending_updates=True)

#         await asyncio.Future()
#     except asyncio.CancelledError:
#         print("Bot task cancelled")
#     except Exception as e:
#         print(f"Bot error: {e}")
#     finally:
#         if app.updater and app.updater.running:
#             await app.updater.stop()
#         await app.stop()
#         await app.shutdown()
#         print("Telegram bot has shut down")

    