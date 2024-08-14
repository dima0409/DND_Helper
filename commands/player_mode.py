from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from commands.keyboards import player_mode_keyboard
from db.db_manager import join_session, get_available_sessions, get_users_in_session

# Обработка команды /player
async def process_player_mode(message: Message):
    await message.answer("Режим игрока. Выберите действие:", reply_markup=player_mode_keyboard)

# Обработка команды присоединения к сессии
async def process_join_session_command(message: Message):
    sessions = await get_available_sessions()
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
    await callback_query.message.edit_text(f"Вы уверены, что хотите присоединиться к сессии '{session_id}'?", reply_markup=keyboard)

# Обработка callback подтверждения присоединения
async def confirm_join_callback_handler(callback_query: CallbackQuery):
    session_id = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id
    success = await join_session(user_id, session_id, "password")
    if success:
        await callback_query.message.edit_text(f"Вы присоединились к сессии '{session_id}'.")
        await callback_query.message.answer(f"{callback_query.from_user.full_name} присоединился к сессии '{session_id}'.")

        # Отправка уведомления всем участникам сессии
        users_in_session = await get_users_in_session(session_id)
        for user in users_in_session:
            if user != user_id:
                await callback_query.bot.send_message(user, f'{callback_query.from_user.full_name} присоединился к сессии "{session_id}".')
    else:
        await callback_query.message.edit_text("Неверный пароль. Подключение не удалось.")
