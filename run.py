import asyncio
from jobs import start_scheduler
from bot import run_bot
from server import run_server

async def main():    
    api_task = asyncio.create_task(run_server())
    bot_task = asyncio.create_task(run_bot())
    scheduler_task = asyncio.create_task(start_scheduler())
    
    await asyncio.gather(api_task, bot_task, scheduler_task)

if __name__ == "__main__":
    asyncio.run(main())
