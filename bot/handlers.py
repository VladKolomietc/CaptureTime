from aiogram import Router, F 
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
import bot.keyboards as kb
from aiogram.fsm.context import FSMContext
import bot.states as st
from aiogram.enums import ParseMode

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
        "<code>dd.mm.yyyy xx:xx \nSong \nAuthor</code>\n\n"
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

@router.message(st.Upl.day_data)
async def Upl_first(message: Message, state: FSMContext):
    await state.update_data(day_data=message.text)
    await state.set_state(st.Upl.confirmation)
    await message.answer(f'Are you sure that your data is: {message.text}?')

@router.message(st.Upl.confirmation)
async def Upl_first(message: Message, state: FSMContext):
    await state.update_data(confirmation=message.text)
    data = await state.get_data()
    await message.answer(f'Thanks! {data["day_data"]} and {data["confirmation"]}')
    await state.clear()
