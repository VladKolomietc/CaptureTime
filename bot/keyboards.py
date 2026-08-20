from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Download'), KeyboardButton(text='Upload')],
    [KeyboardButton(text='Info')]
], resize_keyboard=True, input_field_placeholder='Select a button')