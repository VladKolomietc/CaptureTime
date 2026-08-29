from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Download'), KeyboardButton(text='Upload')],
    [KeyboardButton(text='Info')]
], resize_keyboard=True, input_field_placeholder='Select a button')

downl = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='List', callback_data='listform')]
])

uplo = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Txt', callback_data='txt_upload')],
    [InlineKeyboardButton(text='Photo', callback_data='img_upload')]
])