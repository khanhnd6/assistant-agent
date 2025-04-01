from fastapi import FastAPI, Request
from utils.telegram import sendMessage, sendPhoto
from chat import chat
import asyncio

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "OK"}, 200

@app.post("/telegram")
async def telegram(request: Request):
    try:
        data = await request.json()
        
        message = data['message']
        query = message['text']
        sender_id = message['from']['id']
        
        response = asyncio.run(chat(query, sender_id))
        
        sendMessage(sender_id, response)
    except:
        pass
    finally:
        return {"message": "OK"}, 200