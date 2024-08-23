from aiogram.utils.media_group import MediaGroupBuilder

import db.db_manager
import db.db_manager
from ai.DALLE import *
from commands.general import user_states, form_messages
from commands.info import process_start_command
from commands.keyboards import *
from commands.master_mode import process_master_games, process_enter_description_new_game, \
    process_create_new_game, process_location_generate_image, process_generate_audio, process_npc_generate_image
from commands.pdf_editor import process_pdf_text_input, handle_docs, create_new_character
from commands.player_mode import process_player_games, process_game_request
from db.db_manager import *


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
    elif message.text == 'Мои персонажи':
        if state['mode'] == 'player':
            await handle_docs(message)
        elif state['mode'] == 'master':
            await message.answer(f"Для просмотра персонажей, вы должны быть в режиме игрока!")
        else:
            await message.answer(f"Выберите режим!", reply_markup=main_menu_keyboard)
    elif message.text == "Начать игру (заблокировать подключения)":
        if state['mode'] == 'master':
            await db.db_manager.block_session(message.from_user.id)
            await message.answer("Игра началась!", reply_markup=master_session_locked_keyboard)
            session = await get_user_session(user_id)

            for i in await db.db_manager.get_users_in_session(session.session_id):
                await message.bot.send_message(i[0], "Игра началась!")
        elif state['mode'] == 'player':
            await message.answer(f"В режиме игрока данная команда не доступна!")
        else:
            await message.answer(f"Выберите режим!", reply_markup=main_menu_keyboard)
    elif message.text == "Остановить игру (разблокировать подключения)":
        if state['mode'] == 'master':
            await db.db_manager.block_session(message.from_user.id)
            await message.answer("Игра завершена!", reply_markup=master_session_unlocked_keyboard)
            session = await get_user_session(user_id)

            for i in await db.db_manager.get_users_in_session(session.session_id):
                await message.bot.send_message(i[0], "Игра завершена!")
        elif state['mode'] == 'player':
            await message.answer(f"В режиме игрока данная команда не доступна!")
        else:
            await message.answer(f"Выберите режим!", reply_markup=main_menu_keyboard)
    elif message.text == "Остановить сессию":
        if state['mode'] == 'master':
            await message.answer("Сессия завершена!", reply_markup=master_mode_keyboard)
            session = await get_user_session(user_id)

            for i in await db.db_manager.get_users_in_session(session.session_id):
                user_states[i[0]]['session'] = None
                await message.bot.send_message(i[0], "Сессия завершена!")
            await db.db_manager.stop_session(message.from_user.id)
            state['session'] = None
        elif state['mode'] == 'player':
            await message.answer(f"В режиме игрока данная команда не доступна!")
        else:
            await message.answer(f"Выберите режим!", reply_markup=main_menu_keyboard)

    elif message.text == "Список игроков":
        session = await get_user_session(user_id)
        users = await db.db_manager.get_users_in_session(session.session_id)
        answer = "Игроки в сессии:\n"
        for i in users:
            answer += i[1] + "\n"
        await message.answer(answer)

    else:
        if state['session']:
            user_name = await get_user_name(user_id)
            master = await get_session_master(state['session'])
            players = await get_users_in_session(state['session'])
            players.append(master)
            for i in players:
                if i[0] != user_id:
                    await message.bot.send_message(i[0],
                                                   f'{user_name}: {message.text if message.text is not None else ""}')
                    if message.document:
                        await message.bot.send_document(i[0], message.document.file_id)
                    elif message.sticker:
                        await message.bot.send_sticker(i[0], message.sticker.file_id)
                    elif message.animation:
                        await message.bot.send_animation(i[0], message.animation.file_id)

        if text_expect is None:
            return
        if text_expect == "PDF":
            await process_pdf_text_input(message)
        elif text_expect == "Character_name":
            await create_new_character(user_id, message, message.text)
        elif text_expect == "new_game_name":
            form_messages.append(message.message_id)
            await process_enter_description_new_game(message)
            return
        elif text_expect == "new_game_description":
            form_messages.append(message.message_id)
            await process_create_new_game(message)
            await process_master_games(message)
            await message.bot.delete_messages(user_id, form_messages)
        elif text_expect == "game_request_id":
            await process_game_request(message)
        elif text_expect.startswith("npc_name_"):
            form_messages.append(message.message_id)
            game_id = int(text_expect.removeprefix("npc_name_"))
            state['npc_name'] = message.text
            form_messages.append((await message.answer(f"Введите описание для NPC:")).message_id)
            state['text_expect'] = f"npc_description_{game_id}"
            return
        elif text_expect.startswith("comment_character_"):
            character_id = int(text_expect.removeprefix("comment_character_"))
            character_info = await get_character(character_id)
            await message.bot.send_message(character_info.owner,
                                           f"Комментарий мастера по вашему персонажу {character_info.name}:\n{message.text}")
        elif text_expect.startswith("npc_description_"):
            form_messages.append(message.message_id)
            game_id = int(text_expect.removeprefix("npc_description_"))
            print("description" + str(game_id))
            await create_npc(game_id, state['npc_name'], message.text)
            form_messages.append(message.message_id)
            info = await get_info_about_game(game_id)
            npcs = await get_game_npcs(game_id)
            keyboard = []
            if npcs is not None:
                for npc in npcs:
                    keyboard.append([InlineKeyboardButton(text=npc.name, callback_data=f"npc_{npc.npc_id}")])

            keyboard.append([InlineKeyboardButton(text="Создать нового NPC", callback_data=f"create_npc_{game_id}")])
            keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"materials_{game_id}")])
            await message.answer(
                f"NPC для игры «{info.name}» (id: {info.game_id})",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=keyboard))
            await message.bot.delete_messages(user_id, form_messages)

        elif text_expect.startswith("change_game_name_"):
            form_messages.append(message.message_id)
            game_id = int(text_expect.removeprefix("change_game_name_"))
            await update_game_name(game_id, message.text)
            info = await get_info_about_game(game_id)
            await message.answer(text=f"Игра «{info.name}» (id: {info.game_id})\n{info.description}",
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text="Начать сессию",
                                                           callback_data=f"start_session_{info.game_id}")],
                                     [InlineKeyboardButton(text="Материалы",
                                                           callback_data=f"materials_{info.game_id}")],
                                     [InlineKeyboardButton(text="Изменить название",
                                                           callback_data=f"change_game_name_{info.game_id}")],
                                     [InlineKeyboardButton(text="Изменить описание",
                                                           callback_data=f"change_game_description_{info.game_id}")],
                                     [InlineKeyboardButton(text="Удалить",
                                                           callback_data=f"delete_game_{info.game_id}")]
                                 ]))
            await message.bot.delete_messages(user_id, form_messages)

        elif text_expect.startswith("change_game_description_"):
            form_messages.append(message.message_id)
            game_id = int(text_expect.removeprefix("change_game_description_"))
            await update_game_description(game_id, message.text)
            info = await get_info_about_game(game_id)
            await message.answer(text=f"Игра «{info.name}» (id: {info.game_id})\n{info.description}",
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text="Начать сессию",
                                                           callback_data=f"start_session_{info.game_id}")],
                                     [InlineKeyboardButton(text="Материалы",
                                                           callback_data=f"materials_{info.game_id}")],
                                     [InlineKeyboardButton(text="Изменить название",
                                                           callback_data=f"change_game_name_{info.game_id}")],
                                     [InlineKeyboardButton(text="Изменить описание",
                                                           callback_data=f"change_game_description_{info.game_id}")],
                                     [InlineKeyboardButton(text="Удалить",
                                                           callback_data=f"delete_game_{info.game_id}")]
                                 ]))
            await message.bot.delete_messages(user_id, form_messages)

        elif text_expect.startswith("location_name_"):
            form_messages.append(message.message_id)
            info = text_expect.removeprefix("location_name_")
            state['location_name'] = message.text
            form_messages.append((await message.answer("Введите описание для локации:")).message_id)
            state['text_expect'] = f"location_description_{info}"
            return

        elif text_expect.startswith("location_description_"):
            form_messages.append(message.message_id)
            info = text_expect.removeprefix("location_description_")
            info = info.split('_')
            game_id = info[0]
            parent_id = None
            try:
                parent_id = info[1]
            except:
                pass
            await add_game_location(game_id=game_id, location_name=state['location_name'],
                                    location_description=message.text, parent_location=parent_id)
            await message.bot.delete_messages(user_id, form_messages)
            if parent_id is None:
                locations_list = await get_game_locations_with_parent(game_id, None)
                info = await get_info_about_game(game_id)
                keyboard = []
                if locations_list is not None:
                    for location in locations_list:
                        keyboard.append(
                            [InlineKeyboardButton(text=location.name,
                                                  callback_data=f"location_{location.location_id}")])

                keyboard.append(
                    [InlineKeyboardButton(text="Создать новую локацию", callback_data=f"create_location_{game_id}")])
                keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"materials_{game_id}")])
                await message.answer(f"Локации для игры «{info.name}» (id: {info.game_id})",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            else:
                info = await get_location_info(parent_id)
                keyboard = []
                if info.sub_locations is not None:
                    for location in info.sub_locations:
                        keyboard.append(
                            [InlineKeyboardButton(text=location.name,
                                                  callback_data=f"location_{location.location_id}")])
                keyboard.append([InlineKeyboardButton(text="Посмотреть материалы",
                                                      callback_data=f"show_materials_{location.location_id}")])
                keyboard.append([InlineKeyboardButton(text="Создать изображения",
                                                      callback_data=f"create_locations_images_{info.location_id}")])
                keyboard.append([InlineKeyboardButton(text="Создать звуки окружения",
                                                      callback_data=f"create_locations_sounds_{info.location_id}")])
                keyboard.append(
                    [InlineKeyboardButton(text="Создать новую локацию",
                                          callback_data=f"create_location_{info.game_id}_{info.location_id}")])
                keyboard.append(
                    [InlineKeyboardButton(text="Удалить", callback_data=f"delete_location_{info.location_id}")])
                if info.parent_id is None:
                    keyboard.append(
                        [InlineKeyboardButton(text="← Назад", callback_data=f"list_locations_game_{info.game_id}")])
                else:
                    keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"location_{info.parent_id}")])
                await message.answer(f"Локация {info.name}\n{info.description}\n\nСуб-локации:",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        elif text_expect.startswith("image_prompt_location_"):
            location_id = int(text_expect.removeprefix("image_prompt_location_"))
            await process_location_generate_image(bot=message.bot, user_id=user_id, location_id=location_id,
                                                  prompt=message.text)
        elif text_expect.startswith("sound_prompt_location_"):
            location_id = int(text_expect.removeprefix("sound_prompt_location_"))
            await process_generate_audio(bot=message.bot, user_id=user_id, location_id=location_id, prompt=message.text)
        elif text_expect.startswith("image_prompt_npc_"):
            npc_id = int(text_expect.removeprefix("image_prompt_npc_"))
            await process_npc_generate_image(bot=message.bot, user_id=user_id, npc_id=npc_id, prompt=message.text)
        else:
            return
        state['text_expect'] = None
