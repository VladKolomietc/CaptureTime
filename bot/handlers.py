from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
import bot.keyboards as kb
from aiogram.fsm.context import FSMContext
import bot.states as st
from aiogram.enums import ParseMode
from datetime import datetime
from datab import db
from utils.plotter import generate_activity_plot
import io
import PIL.Image
import asyncio
from utils.ocr import extract_data_from_img

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.add_user(message.from_user.id, message.from_user.username)

    await message.answer('Hey!', reply_markup=kb.main)

@router.message(Command('help'))
async def get_help(message: Message):
    await message.answer('An automated Telegram bot that tracks focus time by parsing iOS lock screen screenshots. It extracts timer data and currently playing music, providing visual analytics and productivity statistics')

@router.message(F.photo)
async def process_screenshot(message: Message, bot: Bot):
    processing_msg = await message.answer("👀 Аналізую скріншот...")
    
    # Беремо останній елемент масиву photo (найкраща якість)
    photo = message.photo[-1]
    
    # Завантажуємо фото в оперативну пам'ять
    photo_bytes = io.BytesIO()
    await bot.download(photo, destination=photo_bytes)
    photo_bytes.seek(0)
    
    # Стискаємо зображення
    img = PIL.Image.open(photo_bytes)
    img.thumbnail((800, 800))
    
    try:
        # Передаємо синхронну функцію в окремий потік, щоб не блокувати aiogram
        data = await asyncio.to_thread(extract_data_from_img, img)
        
        text_result = (
            f"✅ **Розпізнано!**\n"
            f"📅 Дата: {data['captured_at']}\n"
            f"⏱ Фокус: {data['focus_time']}\n"
            f"🎵 Трек: {data['music_title']} - {data['author']}"
        )
        await processing_msg.edit_text(text_result)
        
        # Далі тут буде виклик функції для запису в БД
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Помилка розпізнавання: {e}")

# COMMON FUNCTIONS 

def day_data_validation(parts: list) -> bool:
    if len(parts) > 3:
        return False

    date_string = parts[0].strip()

    try:
        datetime.strptime(date_string, "%d.%m.%Y %H:%M")
    except ValueError:
        try:
                datetime.strptime(date_string, "%d.%m.%y %H:%M")
        except ValueError:
            return False

    return True

def time_display(focus_time: int) -> str:
    hours = focus_time // 60
    minutes = focus_time % 60 
    return f"{hours:02d}:{minutes:02d}"

async def generate_records_text(user_id: int, is_edit_mode: bool) -> str:
    records = await db.user_captures_list(user_id)
    
    text = "<b>Select record ID to change/delete:</b>\n\n" if is_edit_mode else "<b>Your records:</b>\n\n"
            
    for idx, (id, captured_at, focus_time, title, author) in enumerate(records, start=1):
        focus_parsed = time_display(focus_time)
        song_info = f"{title} - {author}" if title and author else "Without music"
        if is_edit_mode:
            text += f"ID:{id} | {captured_at} - {focus_parsed} | {song_info}\n"
        else:
            text += f"{idx}. {captured_at} - {focus_parsed} | {song_info}\n"
    if is_edit_mode:
        text += "\n<i>Enter the actual ID:</i>"
    return text


# DOWNLOAD BLOCK 

@router.message(F.text == 'Download')
async def download_data(message: Message):
    await message.answer('Choose a format of data to download', reply_markup=kb.downl)

@router.callback_query(F.data == 'listform')
async def listform(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')

    text = await generate_records_text(callback.from_user.id, is_edit_mode=False)        
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML)

@router.callback_query(F.data == 'plotform')
async def send_plot(callback: CallbackQuery):
    await callback.answer("Genereting plot... 📊")
    records = await db.user_captures_list(callback.from_user.id)

    if not records:
        await callback.message.edit_text("You don't have any records to plot yet.")
        return 
    
    photo = generate_activity_plot(records)

    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo,
        caption="<b>Your Focus Analytics</b> 📈",
        parse_mode=ParseMode.HTML
    )
    
    
# UPLOAD BLOCK 

@router.message(F.text == 'Upload')
async def upload_data(message: Message, state: FSMContext):
    await state.set_state(st.Upl.day_data)
    await message.answer('Choose a format of data to upload', reply_markup=kb.uplo)

@router.callback_query(F.data == 'txt_upload')
async def txt_upload(callback: CallbackQuery):
    await callback.answer('')
    text = (
        "🕒 <b>New entry for CaptureTime</b>\n\n"
        "Submit your data in the following format:\n"
        "<code>dd.mm.yyyy xx:xx \nSong \nAuthor</code>\n\n"
        "<i>💡Note: song title and artist are optional.</i>"
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
    parts = message.text.split('\n')
    text = (
    "You have entered incorrect data. Please try again following this format -\n\n"
    "<code>dd.mm.yyyy xx:xx\n"
    "Song\n"
    "Author</code>\n\n"
    "The author and title of the song are optional."
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

        captured_at, time_part = (parts[0].strip()).split(" ")
        hours, minutes = map(int, time_part.split(":"))
        focus_time = hours * 60 + minutes

        music_title = parts[1].strip() if len(parts) > 1 else None
        author = parts[2].strip() if len(parts) > 2 else None

        await db.add_capture(message.from_user.id, captured_at, focus_time, music_title, author)

        await message.answer(f'Thanks! We have saved it')
    else: 
        await message.answer(f"Ok, try again. We haven't saved your data")

    await state.clear()
    
# CHANGE/DELETE BLOCK 

@router.message(F.text == "Change/Delete")
async def start_change_flow(message: Message, state: FSMContext):
    await state.set_state(st.ChangeData.select_number)

    text = await generate_records_text(message.from_user.id, is_edit_mode=True)
    await message.answer(text, parse_mode=ParseMode.HTML)

@router.message(st.ChangeData.select_number)
async def choose_action(message: Message, state: FSMContext):
    songID_text = message.text
    if not songID_text.isdigit():
        await message.reply("Entered ID isn't valid. Please enter a number.")
        return

    songID = int(songID_text)

    entry = await db.get_entry(message.from_user.id, songID)
    if not entry:
        await message.reply("Entry with this ID not found.")
        return 

    await state.update_data(select_number=songID)
    rec_id, captured_at, focus_time, title, author = entry[0]

    focus_parsed = time_display(focus_time)
    song_info = f"{title} - {author}" if title and author else "Without music"
    entry_text = f"ID:{rec_id} | {captured_at} - {focus_parsed}| {song_info}"

    text = f"<b>Select the operation you want to apply to this entry:</b>\n{entry_text}"
    await state.set_state(st.ChangeData.action)
    await message.reply(text, parse_mode=ParseMode.HTML, reply_markup=kb.chng_or_del)

@router.callback_query(st.ChangeData.action)
async def change_del(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    songID = data.get("select_number")

    if callback.data == "delete":
        await callback.answer()
        await db.delete_entry(songID)
        await state.clear()
        await callback.message.edit_text("<b>Entry has been deleted</b>", parse_mode=ParseMode.HTML)
    elif callback.data == "change":
        await callback.answer("⏳The feature is under development. ", show_alert=True)
        await state.clear()
    