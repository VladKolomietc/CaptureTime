from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Download'), KeyboardButton(text='Upload')],
    [KeyboardButton(text='Change/Delete')],
    [KeyboardButton(text='Info')]
], resize_keyboard=True, input_field_placeholder='Select a button')

downl = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='List', callback_data='listform')],
    [InlineKeyboardButton(text='Plot', callback_data='plotform')]
])

uplo = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Txt', callback_data='txt_upload')],
    [InlineKeyboardButton(text='Photo', callback_data='img_upload')]
])

chng_or_del = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Change', callback_data='change'), 
     InlineKeyboardButton(text='Delete', callback_data='delete')]
])

