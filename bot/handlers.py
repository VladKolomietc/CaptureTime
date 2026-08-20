from aiogram import Router, F 
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import bot.keyboards as kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Hey!', reply_markup=kb.main)

@router.message(Command('help'))
async def get_help(message: Message):
    await message.answer('An automated Telegram bot that tracks focus time by parsing iOS lock screen screenshots. It extracts timer data and currently playing music, providing visual analytics and productivity statistics')

@router.message(F.photo)
async def get_photo(message: Message):
    await message.reply(f'ID photo: {message.photo[-1].file_id}')