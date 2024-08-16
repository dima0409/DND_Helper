# from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
# # from db.db_manager import start_session, join_session, get_user_session, stop_session, , get_master_session, get_session_by_user, leave_session, user_has_session, get_users_in_session
# from db.db_manager import get_user_session
# async def process_create_command(message: Message):
#     user_id = message.from_user.id
#     if await get_user_session(user_id):
#         await message.answer("Вы уже создали одну сессию. Вы не можете создать больше одной сессии.")
#         return
#
#     session_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
#     if session_name:
#         await create_session(user_id, session_name)
#         await message.answer(f"Сессия '{session_name}' была создана.")
#     else:
#         await message.answer("Пожалуйста, укажите название сессии после команды /create.")
#
# async def process_join_command(message: Message):
#     sessions = await get_sessions()
#     if not sessions:
#         await message.answer("Нет доступных сессий для присоединения.")
#         return
#
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=session, callback_data=f"join_{session}")] for session in sessions
#     ])
#     await message.answer("Выберите сессию для присоединения:", reply_markup=keyboard)
#
# async def join_callback_handler(callback_query: CallbackQuery):
#     session = callback_query.data.split("_")[1]
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_join_{session}")],
#         [InlineKeyboardButton(text="Отмена", callback_data="cancel_join")]
#     ])
#     await callback_query.message.edit_text(f"Вы уверены, что хотите присоединиться к сессии '{session}'?", reply_markup=keyboard)
#
# async def confirm_join_callback_handler(callback_query: CallbackQuery):
#     session = callback_query.data.split("_")[2]
#     user_id = callback_query.from_user.id
#     role = await join_session(user_id, session)
#     await callback_query.message.edit_text(f"Вы присоединились к сессии '{session}' как {role}.")
#     await callback_query.message.answer(f"{callback_query.from_user.full_name} присоединился к сессии '{session}'.")
#
#     # Отправка уведомления всем участникам сессии
#     users_in_session = await get_users_in_session(session)
#     for user in users_in_session:
#         if user != user_id:
#             await callback_query.bot.send_message(user, f'{callback_query.from_user.full_name} присоединился к сессии "{session}".')
#
# async def process_deletesession_command(message: Message):
#     user_id = message.from_user.id
#     session = await get_master_session(user_id)
#     if session:
#         keyboard = InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="Подтвердить удаление", callback_data=f"confirm_delete_{session}")],
#             [InlineKeyboardButton(text="Отмена", callback_data="cancel_delete")]
#         ])
#         await message.answer(f"Вы уверены, что хотите удалить сессию '{session}'?", reply_markup=keyboard)
#     else:
#         await message.answer("Вы не являетесь мастером ни одной сессии или сессия не найдена.")
#
# async def delete_session_callback_handler(callback_query: CallbackQuery):
#     if callback_query.data.startswith("confirm_delete_"):
#         session = callback_query.data.split("_")[2]
#         await delete_session(session)
#         await callback_query.message.edit_text(f"Сессия '{session}' была удалена.")
#
#         # Отправка уведомления всем участникам сессии
#         users_in_session = await get_users_in_session(session)
#         for user in users_in_session:
#             await callback_query.bot.send_message(user, f'Сессия "{session}" была удалена.')
#     elif callback_query.data == "cancel_delete":
#         await callback_query.message.edit_text("Удаление сессии отменено.")
#
# async def process_answer_command(message: Message):
#     user_id = message.from_user.id
#     session = await get_session_by_user(user_id)
#     if session:
#         text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
#         if text:
#             role = await get_role(user_id)
#             role_prefix = "[Мастер] " if role == 'master' else ""
#             full_message = f"{role_prefix}{message.from_user.full_name}: {text}"
#
#             # Отправка сообщения всем участникам сессии
#             users_in_session = await get_users_in_session(session)
#             for user in users_in_session:
#                 await message.bot.send_message(user, full_message)
#         else:
#             await message.answer("Пожалуйста, укажите текст после команды /answer.")
#     else:
#         await message.answer("Вы не присоединились ни к одной сессии.")
#
# async def process_leave_command(message: Message):
#     user_id = message.from_user.id
#     session = await get_session_by_user(user_id)
#     if session:
#         await leave_session(user_id)
#         await message.answer(f"Вы вышли из сессии '{session}'.")
#
#         # Отправка уведомления всем участникам сессии
#         users_in_session = await get_users_in_session(session)
#         for user in users_in_session:
#             await message.bot.send_message(user, f'{message.from_user.full_name} вышел из сессии "{session}".')
#     else:
#         await message.answer("Вы не присоединились ни к одной сессии.")