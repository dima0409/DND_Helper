from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject
from PIL import Image
import fitz  # PyMuPDF
import os

from commands.info import process_start_command
from commands.master_mode import process_master_games, process_start_create_new_game, \
    process_enter_description_new_game, \
    process_create_new_game
from commands.player_mode import process_player_games, process_game_request
from db.db_manager import signup_user, get_user_name, update_game_name, update_game_description, get_info_about_game
from commands.pdf_editor import process_pdf_text_input
from commands.keyboards import master_mode_keyboard, main_menu_keyboard, player_mode_keyboard
from commands.general import user_states


async def process_text_input(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]
    text_expect = state["text_expect"]
    if not await get_user_name(user_id):
        if text_expect != "User_name":
            await process_start_command(message)
            return
        else:
            name = message.text
            state['user_name'] = name
            await signup_user(user_id, name)
            await message.answer(f'Приятно познакомиться, {name}!\nЯ твой верный помощник в игре D&D!\n'
                                 f'Я могу помочь тебе найти компанию для игры, '
                                 f'создать своего персонажа или подготовить материалы для партии!',
                                 reply_markup=main_menu_keyboard)
    if message.text == "Режим мастера":
        state['mode'] = 'master'
        await message.answer(f"Добро пожаловать в режим мастера! Давайте готовиться к партии!",
                             reply_markup=master_mode_keyboard)
        return
    elif message.text == "Режим игрока":
        state['mode'] = 'player'
        await message.answer(f"Добро пожаловать в режим игрока!", reply_markup=player_mode_keyboard)
    elif message.text == "Мои игры":
        if state['mode'] == 'master':
            await process_master_games(message)
        elif state['mode'] == 'player':
            await process_player_games(message)
        else:
            await message.answer(f"Выберите режим!", reply_markup=main_menu_keyboard)
    # elif message.text == ""
    if text_expect is None:
        return
    if text_expect == "PDF":
        await process_pdf_text_input(message)
    elif text_expect == "new_game_name":
        await process_enter_description_new_game(message)
        return
    elif text_expect == "new_game_description":
        await process_create_new_game(message)
    elif text_expect == "game_request_id":
        await process_game_request(message)
    elif text_expect.startswith("change_game_name_"):
        game_id = int(text_expect.removeprefix("change_game_name_"))
        await update_game_name(game_id, message.text)
        info = await get_info_about_game(game_id)
        await message.answer(text=f"Игра «{info.name}» (id: {info.game_id})\n{info.description}",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="Начать сессию",
                                                       callback_data=f"start_session_{info.game_id}")],
                                 [InlineKeyboardButton(text="Материалы", callback_data=f"materials_{info.game_id}")],
                                 [InlineKeyboardButton(text="Изменить название",
                                                       callback_data=f"change_game_name_{info.game_id}")],
                                 [InlineKeyboardButton(text="Изменить описание",
                                                       callback_data=f"change_game_description_{info.game_id}")],
                                 [InlineKeyboardButton(text="Удалить",
                                                       callback_data=f"delete_game_{info.game_id}")]
                             ]))

    elif text_expect.startswith("change_game_description_"):
        game_id = int(text_expect.removeprefix("change_game_description_"))
        await update_game_description(game_id, message.text)
        info = await get_info_about_game(game_id)
        await message.answer(text=f"Игра «{info.name}» (id: {info.game_id})\n{info.description}",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="Начать сессию",
                                                       callback_data=f"start_session_{info.game_id}")],
                                 [InlineKeyboardButton(text="Материалы", callback_data=f"materials_{info.game_id}")],
                                 [InlineKeyboardButton(text="Изменить название",
                                                       callback_data=f"change_game_name_{info.game_id}")],
                                 [InlineKeyboardButton(text="Изменить описание",
                                                       callback_data=f"change_game_description_{info.game_id}")],
                                 [InlineKeyboardButton(text="Удалить",
                                                       callback_data=f"delete_game_{info.game_id}")]
                             ]))
    else:
        return
    state['text_expect'] = None
