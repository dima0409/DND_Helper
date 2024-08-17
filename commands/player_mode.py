from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import db.db_manager
# from commands.keyboards import *
from db.db_manager import *


# Обработка команды /player
# async def process_player_mode(message: Message):
#     await message.answer("Режим игрока. Выберите действие:", reply_markup=player_menu_keyboard)


# Обработка команды присоединения к сессии
async def process_join_session_command(message: Message):
    sessions = await get_available_sessions(message.from_user.id)
    if not sessions:
        await message.answer("Нет доступных сессий для присоединения.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Сессия {session[0]}", callback_data=f"join_{session[0]}")] for session in sessions
    ])
    await message.answer("Выберите сессию для присоединения:", reply_markup=keyboard)


# Обработка callback запроса на присоединение
async def join_callback_handler(callback_query: CallbackQuery):
    session_id = int(callback_query.data.split("_")[1])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_join_{session_id}")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_join")]
    ])
    await callback_query.message.edit_text(f"Вы уверены, что хотите присоединиться к сессии '{session_id}'?",
                                           reply_markup=keyboard)


# Обработка callback подтверждения присоединения
async def confirm_join_callback_handler(callback_query: CallbackQuery):
    session_id = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id
    success = await join_session(user_id, session_id, "password")
    if success:
        await callback_query.message.edit_text(f"Вы присоединились к сессии '{session_id}'.")
        await callback_query.message.answer(
            f"{callback_query.from_user.full_name} присоединился к сессии '{session_id}'.")

        # Отправка уведомления всем участникам сессии
        users_in_session = await get_users_in_session(session_id)
        for user in users_in_session:
            if user != user_id:
                await callback_query.bot.send_message(user,
                                                      f'{callback_query.from_user.full_name} присоединился к сессии "{session_id}".')
    else:
        await callback_query.message.edit_text("Неверный пароль. Подключение не удалось.")


async def process_player_games(message: Message):
    user_id = message.from_user.id
    user_games = await get_users_games_request(user_id, True)
    keyboard_buttons = []
    for i in user_games:
        keyboard_buttons.append([InlineKeyboardButton(text=i.game_name, callback_data=f"player_game_{i.game_id}")])
    keyboard_buttons.append([InlineKeyboardButton(text="Подключиться к игре", callback_data=f"new_game_request")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    if len(user_games) == 0:
        await message.answer("У вас нет игр", reply_markup=keyboard)
        return
    await message.answer(f"Ваши игры:", reply_markup=keyboard)


async def process_game_request(message: Message):
    user_id = message.from_user.id
    user_name = await get_user_name(user_id)
    game_id = int(message.text)
    info = await get_info_about_game(game_id)
    if info.master == user_id:
        await message.answer(f"Вы не можете подключиться к своей же игре!")
        return
    request_id = await send_game_request(user_id, game_id)
    await message.bot.send_message(info.master,
                                   f"На вашу игру «{info.name}» отправлен запрос от пользователя {user_name}",
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [InlineKeyboardButton(text='Одобрить',
                                                             callback_data=f"accept_request_{request_id}"),
                                        InlineKeyboardButton(text='Отклонить',
                                                             callback_data=f"reject_request_{request_id}")]]))
    await message.answer(f"Отправлен запрос на игру «{info.name}»")
