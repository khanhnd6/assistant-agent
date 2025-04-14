from telegram.ext import Application, CallbackContext, MessageHandler, filters
from datetime import datetime, timezone, timedelta
from utils.database import MongoDBConnection
from collections import defaultdict
from dotenv import load_dotenv
from telegram import Update
from chat import chat
import os

SCHEDULER = 60 * 1 #Minutes
load_dotenv()

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message = update.message.text
    response = await chat(message, user_id)
    await update.message.reply_text(str(response))

    photo_path = f"{user_id}_image.jpg"
    if os.path.exists(photo_path):  
        with open(photo_path, "rb") as photo:
            await update.message.reply_photo(photo=photo)
        os.remove(photo_path)

# Lấy ra các thông báo trong thời gian xét hiện tại + 10 phút
def send_notifications(minutes=10):
    try:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        connection = MongoDBConnection(silent=True)
        db = connection.get_database()
        five_minutes = now + timedelta(minutes=minutes)
        query = {"_deleted": False, "_send_notification_at": { "$gte": now, "$lt": five_minutes}}
        records = db["RECORDS"].find(query)
        collection = defaultdict(list)
        for record in records:
            user_id = record["_user_id"]
            clean_data = {k: v for k, v in record.items() if not k.startswith('_')}
            if clean_data: collection[user_id].append(clean_data)

        message = defaultdict(str)
        for user, records in collection.items():
            result = ["🔔 Notification \n"] + [
                f"{idx+1}. " + ". ".join([f"{attr.capitalize()}: {value}" for attr, value in record.items()])
                for idx, record in enumerate(records)
            ]
            message[user] = '\n'.join(result)
        db["RECORDS"].update_many(query, {"$set": {"_send_notification_at": None}})
        connection.close_connection()
        return message
    except Exception as e:
        print(f"Error: {e}")


async def auto_message(context: CallbackContext):
    try:
        collection = send_notifications()
        if collection:
            for user_id, msg in collection.items():
                await context.bot.send_message(chat_id=user_id, text=msg)
        return
    except Exception as e:
        print(f"Lỗi khi gửi tin nhắn tới {user_id}: {e}")

if __name__ == "__main__":
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.job_queue.run_repeating(auto_message, interval=SCHEDULER)
    print(f"🤖 Bot đang chạy và sẽ kiểm tra thông báo mỗi {SCHEDULER} giây")
    app.run_polling()

