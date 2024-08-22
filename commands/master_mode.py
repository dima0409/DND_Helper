from typing import Union

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from ai.DALLE import gen_prompt_by_descriptions, generate_images
from commands.keyboards import master_mode_keyboard
from db.db_manager import *
from commands.general import user_states, form_messages, provide_error


# Обработка команды создания новой игры
async def process_start_create_new_game(callback_query):
    state = user_states[callback_query.from_user.id]
    state['text_expect'] = "new_game_name"
    form_messages.append(
        (await callback_query.bot.send_message(callback_query.from_user.id, "Введите название новой игры:")).message_id)


async def process_enter_description_new_game(message: Message):
    state = user_states[message.from_user.id]
    state['new_game_name'] = message.text
    state['text_expect'] = "new_game_description"
    form_messages.append((await message.answer("Введите описание новой игры:")).message_id)


async def process_create_new_game(message: Message):
    state = user_states[message.from_user.id]
    await create_game(message.from_user.id, state['new_game_name'], message.text)


# Обработка команды мои игры
async def process_master_games(message: Message):
    games = await get_user_games(message.from_user.id)
    for i in games:
        print(i)
    keyboard_buttons = []
    for i in games:
        keyboard_buttons.append([InlineKeyboardButton(text=i.name, callback_data=f"game_{i.game_id}")])
    keyboard_buttons.append([InlineKeyboardButton(text="Создать игру", callback_data=f"create_game")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    if len(games) == 0:
        await message.answer("У вас нет игр", reply_markup=keyboard)
        return
    await message.answer(f"Ваши игры:", reply_markup=keyboard)


async def process_generate_image(bot, user_id, location_id: int, prompt: Union[str, None] = None):
    try:
        if prompt is None:
            location_info = await get_location_info(location_id)
            game_info = await get_info_about_game(location_info.game_id)
            await bot.send_message(user_id, "Уже начали генерировать ваши изображения!")
            prompt = await gen_prompt_by_descriptions(game_description=game_info.description,
                                                      locations_description=location_info.description)

        if prompt is None:
            raise Exception("prompt is None!")
        photo = await generate_images(prompt)
        await bot.send_photo(user_id, caption=f"Использованный промпт - {prompt}", photo=photo,
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Сохранить",
                                                           callback_data=f"save_image_location_{location_id}"),
                                      InlineKeyboardButton(text="Удалить", callback_data=f"location_{location_id}")]]))
    except Exception as e:
        print(e)
        await provide_error(bot, user_id)

# Обработка команды начала сессии
# async def process_start_session(message: Message):
#     await message.answer("Начало сессии пока в разработке.")


# Обработка подтверждения создания игры
# async def process_confirm_game(callback_query: CallbackQuery):
#     # Логика подтверждения создания игры
#     await callback_query.answer("Игра подтверждена.")


# Обработка отмены создания игры
# async def process_cancel_game(callback_query: CallbackQuery):
#     # Логика отмены создания игры
#     await callback_query.answer("Игра отменена.")


# Обработка редактирования игры
# async def process_edit_game(callback_query: CallbackQuery):
#     # Логика редактирования игры
#     await callback_query.answer("Редактирование игры.")


# Обработка команды создания новой сессии
# async def process_create_session_command(message: Message):
#     user_id = message.from_user.id
#     session_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
#     if session_name:
#         await start_session(user_id, session_name, "password")  # Добавьте логику для пароля
#         await message.answer(f"Сессия '{session_name}' была создана.")
#     else:
#         await message.answer("Пожалуйста, укажите название сессии после команды /create_session.")


# Обработка команды удаления сессии
# async def process_deletesession_command(message: Message):
#     user_id = message.from_user.id
#     session = await get_session_master(user_id)  # Используем get_session_master
#     if session:
#         keyboard = InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="Подтвердить удаление", callback_data=f"confirm_delete_{session}")],
#             [InlineKeyboardButton(text="Отмена", callback_data="cancel_delete")]
#         ])
#         await message.answer(f"Вы уверены, что хотите удалить сессию '{session}'?", reply_markup=keyboard)
#     else:
#         await message.answer("Вы не являетесь мастером ни одной сессии или сессия не найдена.")


# Обработка callback подтверждения удаления сессии
# async def delete_session_callback_handler(callback_query: CallbackQuery):
#     if callback_query.data.startswith("confirm_delete_"):
#         session = callback_query.data.split("_")[2]
#         await stop_session(session)
#         await callback_query.message.edit_text(f"Сессия '{session}' была удалена.")
#
#         # Отправка уведомления всем участникам сессии
#         users_in_session = await get_users_in_session(session)
#         for user in users_in_session:
#             await callback_query.bot.send_message(user, f'Сессия "{session}" была удалена.')
#     elif callback_query.data == "cancel_delete":
#         await callback_query.message.edit_text("Удаление сессии отменено.")


# Обработка команды ответа в сессии
# async def process_answer_command(message: Message):
#     user_id = message.from_user.id
#     session = await get_session_master(user_id)  # Получаем сессию мастера
#     if session:
#         text = message.text.split(maxsplit=1)
#         if len(text) > 1:
#             role = "мастер"  # Здесь можно получить роль пользователя (мастер или игрок)
#             role_prefix = f"[{role}] " if role == 'мастер' else ""
#             full_message = f"{role_prefix}{message.from_user.full_name}: {text[1]}"
#
#             # Отправка сообщения всем участникам сессии
#             users_in_session = await get_users_in_session(session)
#             for user in users_in_session:
#                 await message.bot.send_message(user, full_message)
#         else:
#             await message.answer("Пожалуйста, укажите текст после команды /answer.")
#     else:
#         await message.answer("Вы не присоединились ни к одной сессии.")
