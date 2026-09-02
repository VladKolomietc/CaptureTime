import asyncio
import logging
from aiogram import Bot, Dispatcher
from datab import db 
import os
from dotenv import load_dotenv
from bot.handlers import router

async def main():
    load_dotenv() 
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    print(f"Ключ бота завантажено: {bool(BOT_TOKEN)}")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    await db.create_database()
    print('!Database is created successfully!')
    
    print("!Bot is started successfully!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')