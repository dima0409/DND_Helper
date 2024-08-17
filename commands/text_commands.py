from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject
from PIL import Image
import fitz  # PyMuPDF
import os
from db.db_manager import signup_user
from commands.pdf_editor import process_pdf_text_input

from commands.general import user_states


def process_text_input(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]
    text_expect = state["text_expect"]
    if text_expect == "PDF":
        process_pdf_text_input(message)
    elif text_expect == "User_name":
        name = message.text
        state['user_name'] = name
        signup_user(user_id, name)
        message.answer(f'Приятно познакомиться, {name}!\nЯ твой верный помощник в игре D&D!\n'
                       f'Я могу помочь тебе найти компанию для игры, '
                       f'создать своего персонажа или подготовить материалы для партии!')
