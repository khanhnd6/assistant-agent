import os
import asyncio
import requests
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_API_KEY = os.getenv('TELEGRAM_TOKEN')

def send_message(sender_id: int, message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"

    payload = {
        "chat_id": sender_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    headers = {"Content-Type": "application/json"}

    requests.request("POST", url, json=payload, headers=headers)


def send_photo(sender_id: int, photo_url: str, caption: str = '') -> None:

    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendPhoto"

    payload = {
        "chat_id": sender_id,
        # "photo": photo_url,
        "caption": caption
    }
    
    with open(f"{sender_id}_image.jpg", "rb") as photo:
        payload["photo"] = photo

    headers = {"Content-Type": "application/json"}

    requests.request("POST", url, json=payload, headers=headers)
    
async def async_send_message(sender_id: int, message: str) -> None:
    await asyncio.to_thread(send_message, sender_id, message)