from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, ReplyKeyboardMarkup, \
    KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject
from PIL import Image
import fitz  # PyMuPDF
import os
import time
import shutil
from collections import defaultdict
from commands.general import user_states
from commands.info import process_start_command
from commands.keyboards import master_session_unlocked_keyboard
from commands.master_mode import process_start_create_new_game
from db.db_manager import *
from utils.list_utils import find_first


async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    if not get_user_name(user_id):
        await process_start_command(message)
        return
    user_states[user_id] = defaultdict(lambda: None, current_page=0, current_field=None, data_dict={},
                                       messages_to_delete=[])

    # Проверяем, есть ли у пользователя уже созданные персонажи
    existing_characters = await get_user_characters(user_id)

    if existing_characters:
        # Если у пользователя есть хотя бы один персонаж, предлагаем выбор
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Редактировать существующего персонажа", callback_data="edit_existing")
        keyboard.button(text="Создать нового персонажа", callback_data="create_new")
        keyboard.adjust(1)

        await message.reply("У вас уже есть созданные персонажи. Что вы хотите сделать?",
                            reply_markup=keyboard.as_markup())
    else:
        # Если у пользователя нет персонажей, создаем нового
        await create_new_character(user_id, message)


async def create_new_character(user_id, message):
    state = user_states[user_id]
    # Загружаем анкету персонажа D&D из папки other
    file_path = os.path.join('other', 'character_sheet.pdf')

    # Создаем дубликат PDF с именем, содержащим ID пользователя
    edited_file_path = os.path.join('other', f'edited_{time.time()}.pdf')
    shutil.copyfile(file_path, edited_file_path)
    # reader = PdfReader(file_path)
    # print(len(reader.pages))
    # writer = PdfWriter()
    #
    # for i in range(len(reader.pages)):
    #     writer.add_page(reader.pages[i])
    #
    # with open(edited_file_path, 'wb') as output_pdf:
    #     writer.write(output_pdf)
    #

    # Добавляем информацию о новом персонаже в базу данных
    character_name = "New Character"
    state['character_id'] = await add_user_character(user_id, character_name, edited_file_path)

    # Создаем скриншот страницы
    doc = fitz.open(edited_file_path)
    page = doc[0]
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(os.path.join('other', f'page_{user_id}.png'))

    # Отправляем скриншот и кнопки навигации
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Выбрать поле", callback_data="select_field")
    keyboard.button(text="Сохранить", callback_data="save")
    keyboard.button(text="Отмена", callback_data="cancel")
    keyboard.button(text="1", callback_data="page_0")
    keyboard.button(text="2", callback_data="page_1")
    keyboard.button(text="3", callback_data="page_2")
    keyboard.adjust(3, 3)

    await message.reply_photo(FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                              reply_markup=keyboard.as_markup())


async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    state = user_states[user_id]
    current_page = state['current_page']
    current_field = state['current_field']
    data_dict = state['data_dict']
    messages_to_delete = state['messages_to_delete']

    print(callback_query.data)
    if callback_query.data == "edit_existing":
        # Получаем список персонажей пользователя
        characters = await get_user_characters(user_id)
        if not characters:
            await callback_query.message.reply("У вас нет созданных персонажей.")
            return

        # Создаем клавиатуру с кнопками для каждого персонажа
        keyboard = InlineKeyboardBuilder()
        for character in characters:
            keyboard.button(text=character.name, callback_data=f"select_character_{character.character_id}")
        keyboard.button(text="Назад", callback_data="back")
        keyboard.adjust(1)

        await callback_query.message.reply("Выберите персонажа для редактирования:", reply_markup=keyboard.as_markup())

    elif callback_query.data.startswith("select_character_"):
        character_id = int(callback_query.data.split("_")[2])
        state['character_id'] = character_id

        # Получаем путь к файлу из базы данных
        edited_file_path = await get_character_path(character_id)
        if not edited_file_path:
            await callback_query.message.reply("Ошибка: файл не найден.")
            return

        # Создаем скриншот страницы
        doc = fitz.open(edited_file_path)
        page = doc[current_page]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Отправляем скриншот и кнопки навигации
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Выбрать поле", callback_data="select_field")
        keyboard.button(text="Сохранить", callback_data="save")
        keyboard.button(text="Отмена", callback_data="cancel")
        keyboard.button(text="1", callback_data="page_0")
        keyboard.button(text="2", callback_data="page_1")
        keyboard.button(text="3", callback_data="page_2")
        keyboard.adjust(3, 3)

        # Проверяем, содержит ли сообщение медиа перед редактированием
        if callback_query.message.photo or callback_query.message.document:
            await callback_query.message.edit_media(
                InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
                reply_markup=keyboard.as_markup()
            )
        else:
            await callback_query.message.reply_photo(
                photo=FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                reply_markup=keyboard.as_markup()
            )

    elif callback_query.data == "create_new":
        await create_new_character(user_id, callback_query.message)

    elif callback_query.data.startswith("page_"):
        current_page = int(callback_query.data.split("_")[1])
        state['current_page'] = current_page

        # Получаем путь к файлу из базы данных
        edited_file_path = await get_character_path(state['character_id'])
        if not edited_file_path:
            await callback_query.message.reply("Ошибка: файл не найден.")
            return

        # Создаем скриншот страницы
        doc = fitz.open(edited_file_path)
        page = doc[current_page]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Отправляем скриншот и кнопки навигации
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Выбрать поле", callback_data="select_field")
        keyboard.button(text="Сохранить", callback_data="save")
        keyboard.button(text="Отмена", callback_data="cancel")
        keyboard.button(text="1", callback_data="page_0")
        keyboard.button(text="2", callback_data="page_1")
        keyboard.button(text="3", callback_data="page_2")
        keyboard.adjust(3, 3)

        # Проверяем, содержит ли сообщение медиа перед редактированием
        if callback_query.message.photo or callback_query.message.document:
            await callback_query.message.edit_media(
                InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
                reply_markup=keyboard.as_markup()
            )
        else:
            await callback_query.message.reply_photo(
                photo=FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                reply_markup=keyboard.as_markup()
            )

    elif callback_query.data == "select_field":
        keyboard = InlineKeyboardBuilder()
        if current_page == 0:
            fields = ['CharacterName', 'ClassLevel', 'Background', 'PlayerName', 'Race', 'Alignment']
        elif current_page == 1:
            fields = ['ExperiencePoints', 'Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma',
                      'Appearance', 'ClanImage']
        else:
            fields = ['OtherField1', 'OtherField2', 'OtherField3']

        for field in fields:
            keyboard.button(text=field, callback_data=f"field_{field}")
        keyboard.button(text="Назад", callback_data="back")
        keyboard.adjust(1)

        await callback_query.message.edit_reply_markup(reply_markup=keyboard.as_markup())

    elif callback_query.data.startswith("field_"):
        current_field = callback_query.data.split("_")[1]
        state['current_field'] = current_field
        msg = await callback_query.bot.send_message(callback_query.from_user.id,
                                                    f"Введите значение для поля {current_field}:")
        messages_to_delete.append(msg.message_id)

    elif callback_query.data == "confirm":
        edited_file_path = await get_character_path(state['character_id'])
        if not edited_file_path:
            await callback_query.bot.send_message(callback_query.from_user.id, "Ошибка: файл не найден.")
            return

        reader = PdfReader(edited_file_path)
        writer = PdfWriter()

        for i in range(len(reader.pages)):
            page = reader.pages[i]
            writer.update_page_form_field_values(page, fields=data_dict)
            writer.add_page(page)

        with open(edited_file_path, 'wb') as output_pdf:
            writer.write(output_pdf)

        # Создаем скриншот страницы
        doc = fitz.open(edited_file_path)
        page = doc[state['current_page']]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Сохранить", callback_data="save")
        keyboard.button(text="Отмена", callback_data="cancel")
        keyboard.adjust(1)

        await callback_query.bot.send_message(callback_query.from_user.id, "Просмотр редактированной PDF:",
                                              reply_markup=keyboard.as_markup())
        await callback_query.bot.send_document(callback_query.from_user.id,
                                               FSInputFile(edited_file_path))

    elif callback_query.data == "save":
        edited_file_path = await get_character_path(state['character_id'])
        if not edited_file_path:
            await callback_query.bot.send_message(callback_query.from_user.id, "Ошибка: файл не найден.")
            return

        reader = PdfReader(edited_file_path)
        writer = PdfWriter()

        for i in range(len(reader.pages)):
            page = reader.pages[i]
            writer.update_page_form_field_values(page, fields=data_dict)
            writer.add_page(page)

        with open(edited_file_path, 'wb') as output_pdf:
            writer.write(output_pdf)

        await callback_query.bot.send_document(callback_query.from_user.id, FSInputFile(edited_file_path))
        await callback_query.bot.send_message(callback_query.from_user.id, "Изменения сохранены.")

        for msg_id in messages_to_delete:
            await callback_query.bot.delete_message(callback_query.from_user.id, msg_id)
        messages_to_delete.clear()

    elif callback_query.data == "cancel":
        await callback_query.bot.send_message(callback_query.from_user.id, "Изменения отменены.")

        for msg_id in messages_to_delete:
            await callback_query.bot.delete_message(callback_query.from_user.id, msg_id)
        messages_to_delete.clear()

    elif callback_query.data == "back":
        current_page = state['current_page']
        current_field = None
        data_dict = state['data_dict']
        messages_to_delete = state['messages_to_delete']

    elif callback_query.data == "create_game":
        await callback_query.message.delete()
        await process_start_create_new_game(callback_query)
    elif callback_query.data.startswith("game_"):
        game_id = int(callback_query.data.removeprefix("game_"))
        info = await get_info_about_game(game_id)
        await callback_query.message.edit_text(f"Игра «{info.name}» (id: {info.game_id})\n{info.description}")
        await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать сессию", callback_data=f"start_session_{info.game_id}")],
            [InlineKeyboardButton(text="Материалы", callback_data=f"materials_{info.game_id}")],
            [InlineKeyboardButton(text="Изменить название", callback_data=f"change_game_name_{info.game_id}")],
            [InlineKeyboardButton(text="Изменить описание", callback_data=f"change_game_description_{info.game_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete_game_{info.game_id}")]
        ]))
    elif callback_query.data.startswith("change_game_name_"):
        await callback_query.message.delete()
        state['text_expect'] = callback_query.data
        await callback_query.bot.send_message(callback_query.from_user.id, f"Введите новое название игры:")

    elif callback_query.data.startswith("change_game_description_"):
        await callback_query.message.delete()
        state['text_expect'] = callback_query.data
        await callback_query.bot.send_message(callback_query.from_user.id, f"Введите новое описание игры:")
    elif callback_query.data.startswith("delete_game_"):
        game_id = int(callback_query.data.removeprefix("delete_game_"))
        info = await get_info_about_game(game_id)
        await callback_query.message.edit_text(f"Вы уверены что хотите удалить игру «{info.name}»")
        await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="confirm_" + callback_query.data),
             InlineKeyboardButton(text="Нет", callback_data="cancel_" + callback_query.data)]])
        )
    elif callback_query.data.startswith("confirm_delete_game_"):
        game_id = int(callback_query.data.removeprefix("confirm_delete_game_"))
        await delete_game(game_id)
        await callback_query.message.delete()
        games = await get_user_games(callback_query.from_user.id)
        keyboard_buttons = []
        for i in games:
            keyboard_buttons.append([InlineKeyboardButton(text=i.name, callback_data=f"game_{i.game_id}")])
        keyboard_buttons.append([InlineKeyboardButton(text="Создать игру", callback_data=f"create_game")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        if len(games) == 0:
            await callback_query.bot.send_message(callback_query.from_user.id, "У вас нет игр", reply_markup=keyboard)
            return
        await callback_query.bot.send_message(callback_query.from_user.id, f"Ваши игры:", reply_markup=keyboard)
    elif callback_query.data.startswith("cancel_delete_game_"):
        game_id = int(callback_query.data.removeprefix("cancel_delete_game_"))
        info = await get_info_about_game(game_id)
        await callback_query.message.edit_text(f"Игра «{info.name}» (id: {info.game_id})\n{info.description}")
        await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать сессию", callback_data=f"start_session_{info.game_id}")],
            [InlineKeyboardButton(text="Материалы", callback_data=f"materials_{info.game_id}")],
            [InlineKeyboardButton(text="Изменить название", callback_data=f"change_game_name_{info.game_id}")],
            [InlineKeyboardButton(text="Изменить описание", callback_data=f"change_game_description_{info.game_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete_game_{info.game_id}")]
        ]))
    elif callback_query.data.startswith("start_session_"):
        game_id = int(callback_query.data.removeprefix("start_session_"))
        info = await get_info_about_game(game_id)
        state['session'] = await start_session(game_id, 1111, timestamp=time.time_ns())
        await callback_query.bot.send_message(callback_query.from_user.id, f"Начата сессия по игре {info.name}",
                                              reply_markup=master_session_unlocked_keyboard)
        for player in await get_players_in_game(game_id):
            await callback_query.bot.send_message(player, f"Начата сессия по игре {info.name}",
                                                  reply_markup=InlineKeyboardMarkup(
                                                      inline_keyboard=[[InlineKeyboardButton(text="Подключиться",
                                                                                             callback_data=f"session_connect_{game_id}")]]))
    elif callback_query.data == "new_game_request":
        await callback_query.message.delete()
        state['text_expect'] = 'game_request_id'
        await callback_query.bot.send_message(callback_query.from_user.id, "Введите id игры:")

    elif callback_query.data.startswith("accept_request_"):
        request_id = int(callback_query.data.removeprefix("accept_request_"))
        info = await get_game_request(request_id)
        game_info = await get_info_about_game(info[2])
        print("accepting")
        await approve_request(request_id)
        await callback_query.message.delete()
        await callback_query.bot.send_message(info[1],
                                              f"Ваш запрос на подключение к игре «{game_info.name}» был одобрен!")

    elif callback_query.data.startswith("reject_request_"):
        request_id = int(callback_query.data.removeprefix("reject_request_"))
        info = await get_game_request(request_id)
        game_info = await get_info_about_game(info[2])
        print("rejecting")
        await reject_request(request_id)
        await callback_query.message.delete()
        await callback_query.bot.send_message(info[1],
                                              f"Нам очень жаль, но ваш запрос на подключение к игре «{game_info.name}» был отклонен")

    elif callback_query.data.startswith("player_game_"):
        game_id = int(callback_query.data.removeprefix("player_game_"))
        info = await get_info_about_game(game_id)
        is_session = game_id in list(map(lambda x: x.game_id, await get_available_sessions(user_id)))
        await callback_query.message.edit_text(
            f"Игра «{info.name}»{' (идет сессия)' if is_session else ''}\n{info.description}")
        keyboard = []
        if is_session:
            keyboard.append(
                [InlineKeyboardButton(text="Подключиться к сессии", callback_data=f"session_connect_{game_id}")])
        keyboard.append(
            [InlineKeyboardButton(text="Отключиться от игры", callback_data=f"delete_player_game_{game_id}")])
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    elif callback_query.data.startswith("session_connect_"):
        game_id = int(callback_query.data.removeprefix("session_connect_"))
        await join_session(user_id, game_id, 1111)
        info = await get_info_about_game(game_id)
        send_list = await get_players_in_game(game_id)
        send_list.append(info.master)
        user_name = await get_user_name(user_id)
        for user in send_list:
            if user == user_id:
                await callback_query.bot.send_message(user,
                                                      f"{user_name} добро пожаловать в сессию по игре «{info.name}»!")
                continue
            await callback_query.bot.send_message(user, f"{user_name} присоединился к сессии!",
                                                  reply_markup=None if user != info.master else InlineKeyboardMarkup(
                                                      inline_keyboard=[[InlineKeyboardButton(text="Исключить",
                                                                                             callback_data=f'kick_player_{user_id}')]]))
    elif callback_query.data.startswith("materials_"):
        game_id = int(callback_query.data.removeprefix("materials_"))
        info = await get_info_about_game(game_id)
        await callback_query.message.edit_text(
            f"Игра «{info.name}» (id: {info.game_id})\nВыберете какие материалы вас интересуют",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Локации", callback_data=f"list_locations_game_{game_id}")],
                                 [InlineKeyboardButton(text="NPC", callback_data=f"list_NPC_game_{game_id}")],
                                 [InlineKeyboardButton(text="← Назад", callback_data=f"game_{game_id}")]]))
    elif callback_query.data.startswith("list_NPC_game_"):
        game_id = int(callback_query.data.removeprefix("list_NPC_game_"))
        info = await get_info_about_game(game_id)
        npcs = await get_user_npcs(game_id)
        keyboard = []
        if npcs is not None:
            for npc in npcs:
                keyboard.append([InlineKeyboardButton(text=npc.name, callback_data=f"npc_{npc.npc_id}")])

        keyboard.append([InlineKeyboardButton(text="Создать нового NPC", callback_data=f"create_npc_{game_id}")])
        keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"materials_{game_id}")])
        await callback_query.message.edit_text(
            f"NPC для игры «{info.name}» (id: {info.game_id})",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard))

    # elif callback_query.data.startswith("list_locations_game_"):
    #     path = list(map(int, callback_query.data.removeprefix("list_NPC_game_").split("/")))
    #     game_id = path.pop(0)
    #     info = await get_info_about_game(game_id)
    #     locations = await get_game_locations(game_id)
    #     for i in path:
    #         locations = list_utils.find_first(locations, lambda x: x.location_id == i).sub_locations
    #
    #     keyboard = []
    #     for location in locations:
    #         keyboard.append([InlineKeyboardButton(text=location.name, callback_data=f"{npc.npc_id}")])
    #
    #     keyboard.append([InlineKeyboardButton(text="Создать нового NPC", callback_data=f"create_npc_{game_id}")])
    #     keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"materials_{game_id}")])
    #     await callback_query.message.edit_text(
    #         f"NPC для игры «{info.name}» (id: {info.game_id}",
    #         reply_markup=InlineKeyboardMarkup(
    #             inline_keyboard=keyboard))


async def process_pdf_text_input(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]
    current_field = state['current_field']
    data_dict = state['data_dict']
    messages_to_delete = state['messages_to_delete']

    if current_field:
        if current_field in ['Appearance', 'ClanImage']:
            # Обработка изображений
            if message.photo:
                photo = message.photo[-1]
                file_info = await message.bot.get_file(photo.file_id)
                file_path = file_info.file_path
                downloaded_file = await message.bot.download_file(file_path)
                image_path = os.path.join('other', f'{current_field}_{user_id}.png')
                with open(image_path, 'wb') as img_file:
                    img_file.write(downloaded_file.getvalue())
                data_dict[current_field] = image_path
            else:
                await message.bot.send_message(message.from_user.id, "Пожалуйста, отправьте изображение.")
                return
        else:
            data_dict[current_field] = message.text

        state['current_field'] = None
        await message.delete()

        # Удаляем предыдущие сообщения
        for msg_id in messages_to_delete:
            await message.bot.delete_message(message.from_user.id, msg_id)
        messages_to_delete.clear()

        # Отправляем сообщение "Загрузка..."
        loading_msg = await message.bot.send_message(message.from_user.id, "Загрузка...")
        messages_to_delete.append(loading_msg.message_id)

        # Получаем путь к файлу из базы данных
        edited_file_path = await get_character_path(state['character_id'])
        if not edited_file_path:
            await message.bot.send_message(message.from_user.id, "Ошибка: файл не найден.")
            return

        # Обновляем PDF и создаем скриншот
        reader = PdfReader(edited_file_path)
        writer = PdfWriter()

        for i in range(len(reader.pages)):
            page = reader.pages[i]
            writer.update_page_form_field_values(page, fields=data_dict)
            writer.add_page(page)

        with open(edited_file_path, 'wb') as output_pdf:
            writer.write(output_pdf)

        # Создаем скриншот страницы
        doc = fitz.open(edited_file_path)
        page = doc[state['current_page']]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Отладочное сообщение для проверки скриншота
        print(f"Скриншот создан: {os.path.join('other', f'page_{user_id}.png')}")

        # Отправляем скриншот и кнопки навигации
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Выбрать поле", callback_data="select_field")
        keyboard.button(text="Сохранить", callback_data="save")
        keyboard.button(text="Отмена", callback_data="cancel")
        keyboard.button(text="1", callback_data="page_0")
        keyboard.button(text="2", callback_data="page_1")
        keyboard.button(text="3", callback_data="page_2")
        keyboard.adjust(3, 3)

        # Редактируем сообщение "Загрузка..." с новым скриншотом
        await message.bot.edit_message_media(
            media=InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
            chat_id=message.from_user.id,
            message_id=loading_msg.message_id,
            reply_markup=keyboard.as_markup()
        )
