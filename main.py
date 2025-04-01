from fastapi import FastAPI, Request
from utils.telegram import sendMessage, sendPhoto

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
        
        sendMessage(sender_id, query)
    except:
        pass
    finally:
        return {"message": "OK"}, 200