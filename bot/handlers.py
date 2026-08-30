from aiogram import Router, F 
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
import bot.keyboards as kb
from aiogram.fsm.context import FSMContext
import bot.states as st
from aiogram.enums import ParseMode
from datetime import datetime
from datab import db

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.add_user(message.from_user.id, message.from_user.username)

    await message.answer('Hey!', reply_markup=kb.main)

@router.message(Command('help'))
async def get_help(message: Message):
    await message.answer('An automated Telegram bot that tracks focus time by parsing iOS lock screen screenshots. It extracts timer data and currently playing music, providing visual analytics and productivity statistics')

@router.message(F.photo)
async def get_photo(message: Message):
    await message.reply(f'ID photo: {message.photo[-1].file_id}')



# DOWNLOAD BLOCK 

@router.message(F.text == 'Download')
async def download_data(message: Message):
    await message.answer('Choose a format of data to download', reply_markup=kb.downl)

@router.callback_query(F.data == 'listform')
async def listform(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('09.11 - 14:48')



# UPLOAD BLOCK 

@router.message(F.text == 'Upload')
async def upload_data(message: Message, state: FSMContext):
    await state.set_state(st.Upl.day_data)
    await message.answer('Choose a format of data to upload', reply_markup=kb.uplo)

@router.callback_query(F.data == 'txt_upload')
async def txt_upload(callback: CallbackQuery):
    await callback.answer('')
    text = (
        "🕒 <b>Новий запис для CaptureTime</b>\n\n"
        "Надішли свої дані у наступному форматі:\n"
        "<code>dd.mm.yy xx:xx \nSong \nAuthor</code>\n\n"
        "<i>💡 Примітка: назва пісні та автор не є обов'язковими.</i>"
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML)
    
@router.callback_query(F.data == 'img_upload')
async def img_upload(callback: CallbackQuery):
    await callback.answer('')

    reference=FSInputFile('system_photos/reference.jpg')
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=reference,
        caption='Send photo like this one:'
    )

def day_data_validation(parts: list) -> bool:
    if len(parts) > 3:
        return False
    
    try:
        datetime.strptime(parts[0], "%d.%m.%y %H:%M")
    except ValueError:
        return False

    return True
    

@router.message(st.Upl.day_data)
async def Upl_first(message: Message, state: FSMContext):
    parts = message.text.split('\n')
    text = (
    "Ви ввели невірні дані. Спробуйте знову, слідуючи такому формату -\n\n"
    "<code>dd.mm.yyyy xx:xx\n"
    "Song\n"
    "Author</code>\n\n"
    "Автор та назва пісні необов'язкові."
    )   
    if not day_data_validation(parts):
        await message.answer(text, parse_mode=ParseMode.HTML)
        return 

    await state.update_data(day_data=message.text)
    await state.set_state(st.Upl.confirmation)
    await message.answer(f'Are you sure that your data is:\n{message.text}?')

@router.message(st.Upl.confirmation)
async def Upl_second(message: Message, state: FSMContext):
    
    if message.text.lower() == 'yes':
        data = await state.get_data()
        parts = data["day_data"].split('\n')

        captured_at = parts[0]
        music_title = parts[1] if len(parts) > 1 else None
        author = parts[2] if len(parts) > 2 else None

        await db.add_capture(message.from_user.id, captured_at, music_title, author)

        await message.answer(f'Thanks! We have saved it')
    else: 
        await message.answer(f"Ok, try again. We haven't saved your data")

    await state.clear()
    
