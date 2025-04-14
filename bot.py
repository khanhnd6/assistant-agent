from telegram.ext import CommandHandler, MessageHandler, Application, filters, ContextTypes
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from dotenv import load_dotenv
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from chat import chat
import os
import asyncio
import pytz
from datetime import datetime
import logging

from utils.database import MongoDBConnection

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
tf = TimezoneFinder()
geolocator = Nominatim(user_agent="telegram-bot")

if not os.getenv('TELEGRAM_TOKEN'):
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    
    logger.info(f"User {user_id} started the bot")
    
    connection = MongoDBConnection()
    collection = connection.get_database()["USER_PROFILES"]
    
    user_profile = collection.find_one({"user_id": user_id})
    
    if not user_profile:
        new_profile = {
            "user_id": user_id,
            "user_name": user_name,
            "dob": None,
            "region": None,
            "styles": None,
            "interests": None,
            "timezone": None,
            "instructions": None
        }
        collection.insert_one(new_profile)
        location_button = KeyboardButton("📍 Share location", request_location=True)
        reply_markup = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "👋 Welcome! I don't have your timezone yet.\n"
            "- On mobile: tap the button below to share your location.\n"
            "- On web: type your city (e.g., `Hanoi`, `New York`, `Tokyo`) with /settimezone command.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif user_profile.get("timezone"):
        tz = pytz.timezone(user_profile["timezone"])
        local_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(
            f"👋 Welcome back, {user_name}!\n"
            f"Your timezone is set to: `{user_profile['timezone']}`\n"
            f"Current local time: `{local_time}`\n"
            "You can change it with /settimezone or share a new location.",
            parse_mode='Markdown'
        )
    
    else:
        location_button = KeyboardButton("📍 Share location", request_location=True)
        reply_markup = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            f"👋 Welcome back, {user_name}! I don't have your timezone yet.\n"
            "- On mobile: tap the button below to share your location.\n"
            "- On web: type your city (e.g., `Hanoi`, `New York`, `Tokyo`) with /settimezone command.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    connection.close_connection()

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    loc = update.message.location
    lat, lon = loc.latitude, loc.longitude
    tz_name = tf.timezone_at(lat=lat, lng=lon)

    logger.info(f"User {user_id} shared location: ({lat}, {lon})")

    if not tz_name:
        await update.message.reply_text("😕 Sorry, couldn't determine timezone from your location.")
        return

    tz = pytz.timezone(tz_name)
    local_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    connection = MongoDBConnection()
    collection = connection.get_database()["USER_PROFILES"]
    
    user_profile = collection.find_one({"user_id": user_id})
    
    if not user_profile:
        new_profile = {
            "user_id": user_id,
            "user_name": user_name,
            "dob": None,
            "region": None,
            "styles": None,
            "interests": None,
            "timezone": tz_name,
            "instructions": None
        }
        collection.insert_one(new_profile)
    
    else:
        collection.update_one(
            {"user_id": user_id},
            {"$set": {"timezone": tz_name}}
        )
    
    connection.close_connection()
    
    await update.message.reply_text(
        f"Thanks for sharing your location!\n"
        f"*📍 Your timezone* is set to: `{tz_name}`\n"
        f"*🕒 Local time*: `{local_time}`\n"
        "You can continue to chat with your assistant or update your timezone with /settimezone.",
        parse_mode='Markdown'
    )

async def handle_set_time_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    
    if context.args:
        place = ' '.join(context.args).strip().lower()
    else:
        await update.message.reply_text(
            "❗ Please provide a city, e.g. `/settimezone Hanoi`",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"User {user_id} set timezone for place: {place}")

    location = geolocator.geocode(place)
    if not location:
        await update.message.reply_text(
            "🔍 Couldn't find that place. Try a different city or spelling.",
            parse_mode='Markdown'
        )
        return

    tz_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    if not tz_name:
        await update.message.reply_text(
            "😕 Couldn't determine timezone from that location.",
            parse_mode='Markdown'
        )
        return

    tz = pytz.timezone(tz_name)
    local_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    connection = MongoDBConnection()
    collection = connection.get_database()["USER_PROFILES"]
    
    user_profile = collection.find_one({"user_id": user_id})
    
    if not user_profile:
        new_profile = {
            "user_id": user_id,
            "user_name": user_name,
            "dob": None,
            "region": None,
            "styles": None,
            "interests": None,
            "timezone": tz_name,
            "instructions": None
        }
        collection.insert_one(new_profile)
    
    else:
        collection.update_one(
            {"user_id": user_id},
            {"$set": {"timezone": tz_name}}
        )
    
    connection.close_connection()
    
    await update.message.reply_text(
        f"*🌍 Timezone* for '{place.title()}' set to: `{tz_name}`\n"
        f"*🕒 Local time*: `{local_time}`\n"
        "You can continue to chat with your assistant.",
        parse_mode='Markdown'
    )

async def handle_get_time_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    
    logger.info(f"User {user_id} requested timezone")

    connection = MongoDBConnection()
    collection = connection.get_database()["USER_PROFILES"]
    
    user_profile = collection.find_one({"user_id": user_id})
    
    if not user_profile:
        new_profile = {
            "user_id": user_id,
            "user_name": user_name,
            "dob": None,
            "region": None,
            "styles": None,
            "interests": None,
            "timezone": None,
            "instructions": None
        }
        collection.insert_one(new_profile)
        await update.message.reply_text(
            f"👋 Hi, {user_name}! I don't have your timezone yet.\n"
            "Please use /settimezone <city> (e.g., `/settimezone Hanoi`) or share your location with /start.",
            parse_mode='Markdown'
        )
    
    elif user_profile.get("timezone"):
        tz = pytz.timezone(user_profile["timezone"])
        local_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(
            f"*🌍 Your timezone*: `{user_profile['timezone']}`\n"
            f"*🕒 Local time*: `{local_time}`\n"
            "You can update it with /settimezone <city> or share a new location with /start.",
            parse_mode='Markdown'
        )
    
    else:
        await update.message.reply_text(
            f"👋 Hi, {user_name}! I don't have your timezone yet.\n"
            "Please use /settimezone <city> (e.g., `/settimezone Hanoi`) or share your location with /start.",
            parse_mode='Markdown'
        )
    
    connection.close_connection()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_id = update.message.from_user.id
    message = update.message.text
    
    logger.info(f"User {user_id} sent message: {message}")

    response = await chat(message, user_id)
    await update.message.reply_text(str(response), parse_mode='Markdown')

    photo_path = f"{user_id}_image.jpg"
    if os.path.exists(photo_path):
        try:
            with open(photo_path, "rb") as photo:
                await update.message.reply_photo(photo=photo)
            os.remove(photo_path)
        except Exception as e:
            logger.error(f"Failed to send photo for user {user_id}: {e}")

if __name__ == "__main__":
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settimezone", handle_set_time_zone))
    app.add_handler(CommandHandler("mytimezone", handle_get_time_zone))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Starting chatbot...")
    app.run_polling()