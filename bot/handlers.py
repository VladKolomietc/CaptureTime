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
import re

router = Router()

# SAVE FROM IMAGE 

@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.add_user(message.from_user.id, message.from_user.username)

    await message.answer('Hey!', reply_markup=kb.main)

@router.message(Command('help'))
async def get_help(message: Message):
    await message.answer('An automated Telegram bot that tracks focus time by parsing iOS lock screen screenshots. It extracts timer data and currently playing music, providing visual analytics and productivity statistics')

@router.message(Command("exit"))
@router.message(F.text.lower() == "exit")
async def global_cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return 
        
    await state.clear()
    await message.answer("❌ Action canceled. You are back to the main menu.", reply_markup=kb.main)

@router.message(F.photo | F.document)
async def process_screenshot(message: Message, bot: Bot, state: FSMContext):
    processing_msg = await message.answer("👀 Analyzing the screenshot...")

    exact_date = None 
    date_pattern = r"(20\d{2}[-.]\d{2}[-.]\d{2}|\d{2}[-.]\d{2}[-.]20\d{2})"

    if message.caption:
        match = re.search(date_pattern, message.caption)
        if match: 
            exact_date = match.group(1)

    if not exact_date and message.document and message.document.file_name:
        match = re.search(date_pattern, message.document.file_name)
        if match: 
            exact_date = match.group(1)

    # Завантажуємо фото в оперативну пам'ять
    photo_bytes = io.BytesIO()
    if message.photo:
        file = message.photo[-1]
        await bot.download(file, destination=photo_bytes)
    elif message.document and message.document.mime_type.startswith('image/'):
        file = message.document
        await bot.download(file, destination=photo_bytes)
    else:
        await processing_msg.edit_text("❌ The sent file is not an image.")
        return
    photo_bytes.seek(0)
    
    # Стискаємо зображення
    img = PIL.Image.open(photo_bytes)
    img.thumbnail((800, 800))
    
    try:
        # Передаємо синхронну функцію в окремий потік, щоб не блокувати aiogram
        data = await asyncio.to_thread(extract_data_from_img, img)

        if exact_date:
                clean_date = exact_date.replace('-', '.')
                parts = clean_date.split('.')
        
                if len(parts[0]) == 4:
                    formatted_exact_date = f"{parts[2]}.{parts[1]}.{parts[0]}"
                else:
                    formatted_exact_date = f"{parts[0]}.{parts[1]}.{parts[2]}"   
                data['captured_at'] = formatted_exact_date
        
        await state.update_data(
            captured_at=data['captured_at'],
            focus_time=data['focus_time'],
            music_title=data['music_title'],
            author=data['author']
        )
        await state.set_state(st.CaptureProcess.waiting_for_save)

        text_result = (
            f"✅ - Recognized! -\n"
            f"📅 Date: {data['captured_at']}\n"
            f"⏱ Focus: {data['focus_time']}\n"
            f"🎵 Music: {data['music_title']} - {data['author']}"
        )
        
        await processing_msg.edit_text(text_result, reply_markup=kb.save_or_cnl)        
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Recognition error: {e}")

@router.callback_query(F.data == 'save', st.CaptureProcess.waiting_for_save)
async def save_from_img(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await state.get_data()
    await db.add_capture(
        callback.from_user.id, 
        user_data['captured_at'], 
        user_data['focus_time'], 
        user_data['music_title'], 
        user_data['author']
    )
    await callback.message.edit_text(
        f"{callback.message.text}\n\n💾 *Data successfully saved!*",
        parse_mode="Markdown"
    )
    await state.set_state(st.CaptureProcess.waiting_for_save)

@router.callback_query(F.data == 'cancel', st.CaptureProcess.waiting_for_save)
async def cancel_save(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ *The save was cancelled.*",
        parse_mode="Markdown"
    )
    await state.set_state(st.CaptureProcess.waiting_for_save)

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
async def download_data(message: Message, state: FSMContext):
    await state.clear()
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
    await state.clear()
    await message.answer('Choose a format of data to upload', reply_markup=kb.uplo)

@router.callback_query(F.data == 'txt_upload')
async def txt_upload(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await state.set_state(st.CaptureProcess.waiting_for_save)
    text = (
        "🕒 <b>New entry for CaptureTime</b>\n\n"
        "Submit your data in the following format:\n"
        "<code>dd.mm.yyyy xx:xx \nSong \nAuthor</code>\n\n"
        "<i>💡Note: song title and artist are optional.</i>"
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.exit_from_state)
    
@router.callback_query(F.data == 'img_upload')
async def img_upload(callback: CallbackQuery):
    await callback.answer('')

    reference=FSInputFile('system_photos/reference.jpg')
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=reference,
        caption='Send photo like this one:'
    )    

@router.message(st.CaptureProcess.waiting_for_save)
async def Upl_first(message: Message, state: FSMContext):
    if not message.text: return
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
    
    captured_at, focus_time = (parts[0].strip()).split(" ")
            
    music_title = parts[1].strip() if len(parts) > 1 else None
    author = parts[2].strip() if len(parts) > 2 else None
    
    await state.set_state(st.CaptureProcess.waiting_for_save)
    await state.update_data(
        captured_at=captured_at,
        focus_time=focus_time,
        music_title=music_title,
        author=author
    )
    await message.answer(f'Your data is:\n{message.text}', reply_markup=kb.save_or_cnl)
    
# CHANGE/DELETE BLOCK 

@router.message(F.text == "Change/Delete")
async def start_change_flow(message: Message, state: FSMContext):
    await state.clear()
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
        await callback.answer()
        await state.set_state(st.ChangeData.choose_field)
        await callback.message.edit_text("<b>Select what you want to change </b>", reply_markup=kb.change_part, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("edit_"), st.ChangeData.choose_field)
async def choose_edit_field(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    field_map = {
        "edit_date": ("date (fromat DD.MM.YYYY)", "captured_at"),
        "edit_time": ("focus time (format HH:MM)", "focus_time"),
        "edit_title": ("music title", "music_title"),
        "edit_author": ("author", "author")
    }
    
    prompt_text, db_column = field_map[callback.data]
    
    await state.update_data(edit_column=db_column)
    await state.set_state(st.ChangeData.enter_new_values)
    
    await callback.message.edit_text(
        f"Write a new value for: <b>{prompt_text}</b>", 
        parse_mode=ParseMode.HTML
    )

@router.message(st.ChangeData.enter_new_values)
async def process_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    songID = data.get("select_number")
    db_column = data.get("edit_column")
    new_value = message.text.strip()

    if db_column == "captured_at":
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", new_value):
            await message.answer("❌ Incorrect format! Write in DD.MM.YYYY format:")
            return
            
    elif db_column == "focus_time":
        if not re.match(r"^\d{1,2}:\d{2}$", new_value):
            await message.answer("❌ Incorrect format! Write in XX:XX format:")
            return

    await db.update_entry(songID, db_column, new_value)
    
    await message.answer("✅ <b>The entry was successfully updated!</b>", parse_mode=ParseMode.HTML)
    await state.clear()

@router.callback_query(F.data == 'exit')
async def exit_from_state(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("❌ Action canceled. You are back to the main menu.", reply_markup=kb.main)