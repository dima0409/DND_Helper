from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject
from PIL import Image
import fitz  # PyMuPDF
import os
from commands.pdf_editor import process_pdf_text_input

from commands.general import user_states


def process_text_input(message: types.Message):
    state = user_states[message.from_user]
    text_expect = state["text_expect"]
    if text_expect == "PDF":
        process_pdf_text_input(message)
