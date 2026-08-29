import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.config import TOKEN
from bot.handlers import router

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    print("Bot is started successfully!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
    