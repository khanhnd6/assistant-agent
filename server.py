from fastapi import FastAPI, Request, HTTPException
import uvicorn
from contextlib import asynccontextmanager
import os
from chat import chat
from utils.telegram import send_message, send_photo
from scheduler import start_scheduler

app = FastAPI()
scheduler = start_scheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    scheduler.shutdown()


@app.get("/")
async def home():
    return {"message": "OK"}, 200

@app.post("/telegram")
async def telegram(request: Request):
    try:
        data = await request.json()
        if "message" not in data:
            raise HTTPException(status_code=400, detail="No message found in request")
        
        message = data["message"]
        sender_id = message["from"]["id"]
        
        message_text = message["text"]
        
        reply_message = await chat(message_text, sender_id)
        send_message(sender_id, reply_message)
        file_name = f"{sender_id}_image.jpg"
        if os.path.exists(file_name):
            send_photo(sender_id, file_name)
            os.remove(file_name)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
    return {"message": "OK"}, 200

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)