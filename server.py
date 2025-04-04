from fastapi import FastAPI, Request, HTTPException
import uvicorn
import asyncio
from chat import chat
from utils.telegram import send_message
from jobs import start_scheduler

app = FastAPI()
scheduler = None

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
    except Exception as e:
        print(f"Error processing request: {str(e)}")
    return {"message": "OK"}, 200

async def startup_event():
    global scheduler
    scheduler = await start_scheduler()
    print("Scheduler started")

@app.on_event("startup")
async def startup():
    asyncio.create_task(startup_event())

@app.on_event("shutdown")
async def shutdown():
    if scheduler:
        scheduler.shutdown()
        print("Scheduler stopped")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)