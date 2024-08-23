from fnmatch import translate

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

from aiogram.utils.media_group import MediaGroupBuilder

from ai.DALLE import gen_dalle_prompt_by_descriptions, generate_images
from commands.general import user_states, form_messages
from commands.info import process_start_command
from commands.keyboards import master_session_unlocked_keyboard, master_session_locked_keyboard
from commands.master_mode import process_start_create_new_game, process_location_generate_image, process_generate_audio, \
    process_npc_generate_image
from db.db_manager import *
from utils.list_utils import find_first

main_fields = ['CharacterName', 'ClassLevel', 'Background', 'PlayerName', 'Race', 'Alignment', 'ExperiencePoints',
               'ProfBonus']
main_translated_fields = ['Имя персонажа', 'Класс и уровень', 'Предыстория', 'Имя игрока', 'Раса',
                          'Мировоззрение', 'Опыт', 'Бонус мастерства']

characteristics_fields = {'Сила': ('STRmod', 'Strength'), 'Ловкость': ('DEXmod', 'Dexterity'),
                          'Телосложение': ('CONmod', 'Constitution'), 'Интеллект': ('INTmod', 'Intelligence'),
                          'Мудрость': ('WISmod', 'Wisdom'), 'Харизма': ('CHamod', 'Charisma')}


async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    if not await get_user_name(user_id):
        await process_start_command(message)
        return

    # Проверяем, есть ли у пользователя уже созданные персонажи
    existing_characters = await get_user_characters(user_id)

    keyboard = InlineKeyboardBuilder()
    if existing_characters:
        for character in existing_characters:
            keyboard.button(text=character.name, callback_data=f"select_character_{character.character_id}")
    keyboard.button(text="Создать нового", callback_data="create_new_character")
    keyboard.adjust(1)

    if not existing_characters:
        await message.answer("У вас нет созданных персонажей", reply_markup=keyboard.as_markup())
        return

    # Создаем клавиатуру с кнопками для каждого персонажа

    await message.answer("Ваши персонажи:", reply_markup=keyboard.as_markup())


async def create_new_character(user_id, message, name="New Character"):
    state = user_states[user_id]
    # Загружаем анкету персонажа D&D из папки other
    file_path = os.path.join('other', 'character_sheet.pdf')

    # Создаем дубликат PDF
    edited_file_path = os.path.join('other', f'characters_sheet_{time.time()}.pdf')
    shutil.copyfile(file_path, edited_file_path)

    # Добавляем информацию о новом персонаже в базу данных
    character_name = name
    character_id = await add_user_character(user_id, character_name, edited_file_path)
    state['character_id'] = character_id
    # Создаем скриншот страницы
    doc = fitz.open(edited_file_path)
    page = doc[0]
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(os.path.join('other', f'page_{user_id}.png'))

    # Отправляем скриншот и кнопки навигации
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="←", callback_data=f"page3_{character_id}"),
         InlineKeyboardButton(text="→", callback_data=f"page2_{character_id}")],
        [InlineKeyboardButton(text="Изменить", callback_data=f"edit_character_{character_id}")],
        [InlineKeyboardButton(text="Экспортировать", callback_data=f"export_character_{character_id}")],
        [InlineKeyboardButton(text="Отправить мастеру", callback_data=f"send_master_{state['character_id']}")],
        [InlineKeyboardButton(text="← Назад", callback_data=f"my_characters")]])

    await message.reply_photo(FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                              reply_markup=keyboard)


async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    state = user_states[user_id]
    current_page = state['current_page']
    current_field = state['current_field']
    data_dict = state['data_dict']
    messages_to_delete = state['messages_to_delete']

    if messages_to_delete is None:
        messages_to_delete = []

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
            await callback_query.bot.send_message(user_id, "Ошибка: файл не найден.")
            return

        # Создаем скриншот страницы
        doc = fitz.open(edited_file_path)
        page = doc[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Отправляем скриншот и кнопки навигации
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data=f"page3_{character_id}"),
             InlineKeyboardButton(text="→", callback_data=f"page2_{character_id}")],
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit_character_{character_id}")],
            [InlineKeyboardButton(text="Экспортировать", callback_data=f"export_character_{character_id}")],
            [InlineKeyboardButton(text="Отправить мастеру", callback_data=f"send_master_{state['character_id']}")],
            [InlineKeyboardButton(text="← Назад", callback_data=f"my_characters")]])

        # Проверяем, содержит ли сообщение медиа перед редактированием
        if callback_query.message.photo or callback_query.message.document:
            await callback_query.message.edit_media(
                InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
                reply_markup=keyboard
            )
        else:
            await callback_query.message.delete()
            await callback_query.bot.send_photo(user_id,
                                                photo=FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                                                reply_markup=keyboard
                                                )

    elif callback_query.data == "create_new_character":
        await callback_query.bot.send_message(user_id, f"Введите имя для персонажа:")
        state['text_expect'] = 'Character_name'
        # await create_new_character(user_id, callback_query.message)
    elif callback_query.data == "my_characters":
        await callback_query.message.delete()
        existing_characters = await get_user_characters(user_id)

        keyboard = InlineKeyboardBuilder()
        for character in existing_characters:
            keyboard.button(text=character.name, callback_data=f"select_character_{character.character_id}")
        keyboard.button(text="Создать нового", callback_data="create_new_character")
        keyboard.adjust(1)

        if not existing_characters:
            await callback_query.bot.send_message(user_id, "У вас нет созданных персонажей",
                                                  reply_markup=keyboard.as_markup())
            return

        # Создаем клавиатуру с кнопками для каждого персонажа

        await callback_query.bot.send_message(user_id, "Ваши персонажи:", reply_markup=keyboard.as_markup())
    elif callback_query.data.startswith("page1_"):
        current_page = 0
        character_id = int(callback_query.data.split("_")[1])
        state['current_page'] = current_page

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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data=f"page3_{character_id}"),
             InlineKeyboardButton(text="→", callback_data=f"page2_{character_id}")],
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit_character_{character_id}")],
            [InlineKeyboardButton(text="Экспортировать", callback_data=f"export_character_{character_id}")],
            [InlineKeyboardButton(text="Отправить мастеру", callback_data=f"send_master_{state['character_id']}")],
            [InlineKeyboardButton(text="← Назад", callback_data=f"my_characters")]])

        # Проверяем, содержит ли сообщение медиа перед редактированием
        if callback_query.message.photo or callback_query.message.document:
            await callback_query.message.edit_media(
                InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
                reply_markup=keyboard
            )
        else:
            await callback_query.message.reply_photo(
                photo=FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                reply_markup=keyboard
            )

    elif callback_query.data.startswith("page2_"):
        current_page = 1
        character_id = int(callback_query.data.split("_")[1])
        state['current_page'] = current_page

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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data=f"page1_{character_id}"),
             InlineKeyboardButton(text="→", callback_data=f"page3_{character_id}")],
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit_character_{character_id}")],
            [InlineKeyboardButton(text="Экспортировать", callback_data=f"export_character_{character_id}")],
            [InlineKeyboardButton(text="Отправить мастеру", callback_data=f"send_master_{state['character_id']}")],
            [InlineKeyboardButton(text="← Назад", callback_data=f"my_characters")]])

        # Проверяем, содержит ли сообщение медиа перед редактированием
        if callback_query.message.photo or callback_query.message.document:
            await callback_query.message.edit_media(
                InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
                reply_markup=keyboard
            )
        else:
            await callback_query.message.reply_photo(
                photo=FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                reply_markup=keyboard
            )

    elif callback_query.data.startswith("page3_"):
        current_page = 2
        character_id = int(callback_query.data.split("_")[1])
        state['current_page'] = current_page

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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data=f"page2_{character_id}"),
             InlineKeyboardButton(text="→", callback_data=f"page1_{character_id}")],
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit_character_{character_id}")],
            [InlineKeyboardButton(text="Экспортировать", callback_data=f"export_character_{character_id}")],
            [InlineKeyboardButton(text="Отправить мастеру", callback_data=f"send_master_{state['character_id']}")],
            [InlineKeyboardButton(text="← Назад", callback_data=f"my_characters")]])

        # Проверяем, содержит ли сообщение медиа перед редактированием
        if callback_query.message.photo or callback_query.message.document:
            await callback_query.message.edit_media(
                InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
                reply_markup=keyboard
            )
        else:
            await callback_query.message.reply_photo(
                photo=FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                reply_markup=keyboard
            )

    elif callback_query.data.startswith("edit_character_"):
        character_id = int(callback_query.data.removeprefix("edit_character_"))
        keyboard = InlineKeyboardBuilder()

        for field, translated_field in zip(main_fields, main_translated_fields):
            keyboard.button(text=translated_field, callback_data=f"field_{field}_{character_id}")
        keyboard.button(text="Характеристики", callback_data=f"characteristics_character_{character_id}")
        keyboard.button(text="Спасброски", callback_data=f"SP_character_{character_id}")
        keyboard.button(text="Навыки", callback_data=f"Skills_character_{character_id}")
        keyboard.button(text="← Назад", callback_data=f"select_character_{character_id}")
        keyboard.adjust(1)

        await callback_query.message.edit_reply_markup(reply_markup=keyboard.as_markup())

    elif callback_query.data.startswith("characteristics_character_"):
        character_id = int(callback_query.data.removeprefix("characteristics_character_"))
        keyboard = InlineKeyboardBuilder()

        for field in characteristics_fields.keys():
            keyboard.button(text=field, callback_data=f"characteristic_{field}_{character_id}")
        keyboard.button(text="← Назад", callback_data=f"edit_character_{character_id}")
        keyboard.adjust(1)
        await callback_query.message.edit_reply_markup(reply_markup=keyboard.as_markup())

    elif callback_query.data.startswith("characteristic_"):
        field, character_id = callback_query.data.split('_')[1:]

        state['character_id'] = character_id
        state['current_field'] = field
        state["text_expect"] = "PDF"

        msg = await callback_query.bot.send_message(callback_query.from_user.id,
                                                    f"Введите значение для поля {field}:")
        form_messages.append(msg.message_id)
        await callback_query.message.delete()

    elif callback_query.data.startswith("field_"):
        current_field, character_id = callback_query.data.removeprefix("field_").split('_')
        character_id = int(character_id)
        state['character_id'] = character_id
        state['current_field'] = current_field
        state["text_expect"] = "PDF"
        index = main_fields.index(current_field)
        if index != -1:
            translated_name = main_translated_fields[index]
        else:
            await callback_query.bot.send_message(callback_query.from_user.id, "Error")
            return

        msg = await callback_query.bot.send_message(callback_query.from_user.id,
                                                    f"Введите значение для поля {translated_name}:")
        form_messages.append(msg.message_id)
        await callback_query.message.delete()

    # elif callback_query.data == "confirm":
    #     edited_file_path = await get_character_path(state['character_id'])
    #     if not edited_file_path:
    #         await callback_query.bot.send_message(callback_query.from_user.id, "Ошибка: файл не найден.")
    #         return
    #
    #     reader = PdfReader(edited_file_path)
    #     writer = PdfWriter()
    #     writer.set_need_appearances_writer()
    #
    #     for i in range(len(reader.pages)):
    #         page = reader.pages[i]
    #         writer.set_need_appearances_writer()
    #
    #         writer.update_page_form_field_values(page, fields=data_dict)
    #         writer.add_page(page)
    #     writer.set_need_appearances_writer()
    #     with open(edited_file_path, 'wb') as output_pdf:
    #         writer.write(output_pdf)
    #
    #     # Создаем скриншот страницы
    #     doc = fitz.open(edited_file_path)
    #     page = doc[state['current_page']]
    #     pix = page.get_pixmap()
    #     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    #     img.save(os.path.join('other', f'page_{user_id}.png'))
    #
    #     keyboard = InlineKeyboardBuilder()
    #     keyboard.button(text="Сохранить", callback_data="save")
    #     keyboard.button(text="Отмена", callback_data="cancel")
    #     keyboard.adjust(1)
    #
    #     await callback_query.bot.send_message(callback_query.from_user.id, "Просмотр редактированной PDF:",
    #                                           reply_markup=keyboard.as_markup())
    #     await callback_query.bot.send_document(callback_query.from_user.id,
    #                                            FSInputFile(edited_file_path))
    #
    # elif callback_query.data == "save":
    #     edited_file_path = await get_character_path(state['character_id'])
    #     if not edited_file_path:
    #         await callback_query.bot.send_message(callback_query.from_user.id, "Ошибка: файл не найден.")
    #         return
    #
    #     reader = PdfReader(edited_file_path)
    #     writer = PdfWriter()
    #     writer.set_need_appearances_writer()
    #     for i in range(len(reader.pages)):
    #         page = reader.pages[i]
    #         writer.set_need_appearances_writer()
    #         writer.update_page_form_field_values(page, fields=data_dict)
    #         writer.add_page(page)
    #     writer.set_need_appearances_writer()
    #     with open(edited_file_path, 'wb') as output_pdf:
    #         writer.write(output_pdf)
    #
    #     await callback_query.bot.send_document(callback_query.from_user.id, FSInputFile(edited_file_path))
    #     await callback_query.bot.send_message(callback_query.from_user.id, "Изменения сохранены.")
    #
    #     for msg_id in messages_to_delete:
    #         await callback_query.bot.delete_message(callback_query.from_user.id, msg_id)
    #     messages_to_delete.clear()

    elif callback_query.data.startswith("export_character_"):
        character_id = int(callback_query.data.removeprefix("export_character_"))
        edited_file_path = await get_character_path(character_id)
        if not edited_file_path:
            await callback_query.bot.send_message(callback_query.from_user.id, "Ошибка: файл не найден.")
            return

        await callback_query.bot.send_document(callback_query.from_user.id, FSInputFile(edited_file_path))

    # elif callback_query.data == "cancel":
    #     await callback_query.bot.send_message(callback_query.from_user.id, "Изменения отменены.")
    #
    #     for msg_id in messages_to_delete:
    #         await callback_query.bot.delete_message(callback_query.from_user.id, msg_id)
    #     messages_to_delete.clear()
    #
    # elif callback_query.data == "back":
    #     current_page = state['current_page']
    #     current_field = None
    #     data_dict = state['data_dict']
    #     messages_to_delete = state['messages_to_delete']
    elif callback_query.data.startswith("send_master_"):
        character_id = int(callback_query.data.removeprefix("send_master_"))
        await callback_query.message.delete()
        games = await get_users_games_request(user_id, True)
        if len(games) == 0:
            await callback_query.bot.send_message(user_id, "Пока что вы не присоединились ни к одной игре :(")
            return
        keyboard = []
        for i in games:
            keyboard.append([InlineKeyboardButton(text=i.game_name,
                                                  callback_data=f"send_character_master_{character_id}_{i.game_id}")])
        await callback_query.bot.send_message(user_id, f"Выберете мастеру какой игры вы хотите отправить персонажа:",
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    elif callback_query.data.startswith("send_character_master_"):
        character_id, game_id = callback_query.data.removeprefix("send_character_master_").split('_')
        character_id, game_id = int(character_id), int(game_id)
        game_info = await get_info_about_game(game_id)
        user_name = await get_user_name(user_id)
        character_info = await get_character(character_id)
        await callback_query.bot.send_document(game_info.master, document=FSInputFile(character_info.path),
                                               caption=f"Пользователь {user_name} отправил персонажа {character_info.name} для вашей игры {game_info.name}",
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                                                   text="Прокомментировать",
                                                   callback_data=f"comment_character_{character_id}")]]))
        await callback_query.message.delete()
        await callback_query.bot.send_message(user_id, "Персонаж отправлен мастеру!")

    elif callback_query.data.startswith("comment_character_"):
        character_id = int(callback_query.data.removeprefix("comment_character_"))
        state['text_expect'] = f"comment_character_{character_id}"
        form_messages.append((await callback_query.bot.send_message(user_id, f"Введите комментарий:")).message_id)

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
        form_messages.append((await callback_query.bot.send_message(callback_query.from_user.id,
                                                                    f"Введите новое название игры:")).message_id)

    elif callback_query.data.startswith("change_game_description_"):
        await callback_query.message.delete()
        state['text_expect'] = callback_query.data
        form_messages.append((await callback_query.bot.send_message(callback_query.from_user.id,
                                                                    f"Введите новое описание игры:")).message_id)
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
        try:
            state['session'] = await start_session(game_id, 1111, timestamp=time.time_ns())
            await callback_query.bot.send_message(callback_query.from_user.id, f"Начата сессия по игре {info.name}",
                                                  reply_markup=master_session_unlocked_keyboard)
            for player in await get_players_in_game(game_id):
                await callback_query.bot.send_message(player, f"Начата сессия по игре {info.name}",
                                                      reply_markup=InlineKeyboardMarkup(
                                                          inline_keyboard=[[InlineKeyboardButton(text="Подключиться",
                                                                                                 callback_data=f"session_connect_{game_id}")]]))
        except:
            session = await get_user_session(user_id)
            info = await get_info_about_game(session.game_id)
            await callback_query.bot.send_message(callback_query.from_user.id,
                                                  f"Вы уже находитесь в сессии по игре {info.name}",
                                                  reply_markup=master_session_locked_keyboard if session.in_progress else master_session_unlocked_keyboard)
            state['session'] = session.session_id

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
        state['session'] = (await get_user_session(user_id)).session_id
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
        npcs = await get_game_npcs(game_id)
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
    elif callback_query.data.startswith("npc_"):
        npc_id = int(callback_query.data.removeprefix("npc_"))
        npc_info = await get_npc_info(npc_id)
        keyboard = [[InlineKeyboardButton(text="Посмотреть материалы",
                                          callback_data=f"show_npc_materials_{npc_id}")],
                    [InlineKeyboardButton(text="Создать изображения",
                                          callback_data=f"images_npc_create_{npc_id}")],
                    [InlineKeyboardButton(text="Удалить", callback_data=f"delete_npc_{npc_id}")],
                    [InlineKeyboardButton(text="← Назад", callback_data=f"list_NPC_game_{npc_info.game_id}")]]
        await callback_query.message.edit_text(
            f"NPC {npc_info.name} для игры {npc_info.game_name}\n{npc_info.description}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    elif callback_query.data.startswith("kick_player_"):
        player_id = int(callback_query.data.removeprefix("kick_player_"))
        name = await get_user_name(player_id)
        await leave_session(player_id)
        await callback_query.bot.send_message(player_id, f"Сожалеем, но вы были исключены из сессии!")
        await callback_query.bot.send_message(user_id, f"Игрок {name} был исключен!")
        user_states[player_id]['session'] = None
    elif callback_query.data.startswith("create_npc_"):
        game_id = int(callback_query.data.removeprefix("create_npc_"))
        state['text_expect'] = f"npc_name_{game_id}"
        form_messages.append(
            (await callback_query.bot.send_message(user_id, f"Введите имя для нового NPC:")).message_id)
        await callback_query.message.delete()
    elif callback_query.data.startswith("delete_npc_"):
        npc_id = int(callback_query.data.removeprefix("delete_npc_"))
        npc_info = await get_npc_info(npc_id)
        await callback_query.message.edit_text(f"Вы уверены, что хотите удалить NPC по имени {npc_info.name}?",
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                                                   text="Удалить", callback_data=f"confirm_remove_npc_{npc_id}"),
                                                   InlineKeyboardButton(
                                                       text="Отмена",
                                                       callback_data=f"npc_{npc_id}")]]))
    elif callback_query.data.startswith("confirm_remove_npc_"):
        npc_id = int(callback_query.data.removeprefix("confirm_remove_npc_"))
        npc_info = await get_npc_info(npc_id)
        game_id = npc_info.game_id

        await delete_npc(npc_id)

        info = await get_info_about_game(game_id)
        npcs = await get_game_npcs(game_id)
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

    elif callback_query.data.startswith("list_locations_game_"):
        game_id = int(callback_query.data.removeprefix("list_locations_game_"))
        locations_list = await get_game_locations_with_parent(game_id, None)
        info = await get_info_about_game(game_id)
        keyboard = []
        if locations_list is not None:
            for location in locations_list:
                keyboard.append(
                    [InlineKeyboardButton(text=location.name, callback_data=f"location_{location.location_id}")])

        keyboard.append(
            [InlineKeyboardButton(text="Создать новую локацию", callback_data=f"create_location_{game_id}")])
        keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"materials_{game_id}")])
        await callback_query.message.edit_text(f"Локации для игры «{info.name}» (id: {info.game_id})",
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    elif callback_query.data.startswith("create_location_"):
        info = callback_query.data.removeprefix("create_location_")
        await callback_query.message.delete()

        form_messages.append(
            (await callback_query.bot.send_message(user_id, f"Введите название для новой локации:")).message_id)
        state['text_expect'] = f'location_name_{info}'
    elif callback_query.data.startswith("location_"):
        location_id = int(callback_query.data.removeprefix("location_"))
        info = await get_location_info(location_id)
        keyboard = []
        if info.sub_locations is not None:
            for location in info.sub_locations:
                keyboard.append(
                    [InlineKeyboardButton(text=location.name, callback_data=f"location_{location.location_id}")])
        keyboard.append([InlineKeyboardButton(text="Посмотреть материалы",
                                              callback_data=f"show_materials_{location_id}")])
        keyboard.append([InlineKeyboardButton(text="Создать изображения",
                                              callback_data=f"create_locations_images_{location_id}")])
        keyboard.append([InlineKeyboardButton(text="Создать звуки окружения",
                                              callback_data=f"create_locations_sounds_{location_id}")])
        keyboard.append(
            [InlineKeyboardButton(text="Создать новую локацию",
                                  callback_data=f"create_location_{info.game_id}_{location_id}")])
        keyboard.append([InlineKeyboardButton(text="Удалить", callback_data=f"delete_location_{location_id}")])
        if info.parent_id is None:
            keyboard.append(
                [InlineKeyboardButton(text="← Назад", callback_data=f"list_locations_game_{info.game_id}")])
        else:
            keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"location_{info.parent_id}")])
        await callback_query.message.edit_text(f"Локация {info.name}\n{info.description}\n\nСуб-локации:",
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    elif callback_query.data.startswith("delete_location_"):
        location_id = int(callback_query.data.removeprefix("delete_location_"))
        await callback_query.message.edit_text("Подтвердите удаление локации", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_delete_location_{location_id}"),
                 InlineKeyboardButton(text="Отменить", callback_data=f"location_{location_id}")]]))
    elif callback_query.data.startswith("confirm_delete_location_"):
        location_id = int(callback_query.data.removeprefix("confirm_delete_location_"))
        info = await get_location_info(location_id)
        await delete_location(location_id)
        if info.parent_id is None:
            locations_list = await get_game_locations_with_parent(info.game_id, None)
            info = await get_info_about_game(info.game_id)
            keyboard = []
            if locations_list is not None:
                for location in locations_list:
                    keyboard.append(
                        [InlineKeyboardButton(text=location.name, callback_data=f"location_{location.location_id}")])

            keyboard.append(
                [InlineKeyboardButton(text="Создать новую локацию", callback_data=f"create_location_{info.game_id}")])
            keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"materials_{info.game_id}")])
            await callback_query.message.edit_text(f"Локации для игры «{info.name}» (id: {info.game_id})",
                                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        else:
            location_id = info.parent_id
            info = await get_location_info(location_id)
            keyboard = []
            if info.sub_locations is not None:
                for location in info.sub_locations:
                    keyboard.append(
                        [InlineKeyboardButton(text=location.name, callback_data=f"location_{location.location_id}")])

            keyboard.append([InlineKeyboardButton(text="Посмотреть материалы",
                                                  callback_data=f"show_materials_{location_id}")])
            keyboard.append([InlineKeyboardButton(text="Создать изображения",
                                                  callback_data=f"create_locations_images_{location_id}")])
            keyboard.append([InlineKeyboardButton(text="Создать звуки окружения",
                                                  callback_data=f"create_locations_sounds_{location_id}")])
            keyboard.append(
                [InlineKeyboardButton(text="Создать новую локацию",
                                      callback_data=f"create_location_{info.game_id}_{location_id}")])
            keyboard.append([InlineKeyboardButton(text="Удалить", callback_data=f"delete_location_{location_id}")])
            if info.parent_id is None:
                keyboard.append(
                    [InlineKeyboardButton(text="← Назад", callback_data=f"list_locations_game_{info.game_id}")])
            else:
                keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"location_{info.parent_id}")])
            await callback_query.message.edit_text(f"Локация {info.name}\n{info.description}\n\nСуб-локации:",
                                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    elif callback_query.data.startswith("create_locations_images_"):
        location_id = int(callback_query.data.removeprefix("create_locations_images_"))
        await callback_query.message.edit_text(f"Выберите способ генерации изображения",
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                   [InlineKeyboardButton(text="Сгенерировать промпт на основе описаний",
                                                                         callback_data=f"description_create_locations_images_{location_id}")],
                                                   [InlineKeyboardButton(text="Мой промпт",
                                                                         callback_data=f"user_prompt_create_locations_images_{location_id}")]]))

    elif callback_query.data.startswith("images_npc_create_"):
        npc_id = int(callback_query.data.removeprefix("images_npc_create_"))
        await callback_query.message.edit_text(f"Выберите способ генерации изображения",
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                   [InlineKeyboardButton(text="Сгенерировать промпт на основе описаний",
                                                                         callback_data=f"description_create_npc_images_{npc_id}")],
                                                   [InlineKeyboardButton(text="Мой промпт",
                                                                         callback_data=f"user_prompt_create_npc_images_{npc_id}")]]))

    elif callback_query.data.startswith("description_create_npc_images_"):
        location_id = int(callback_query.data.removeprefix("description_create_npc_images_"))
        await process_npc_generate_image(bot=callback_query.bot, user_id=user_id, npc_id=location_id)

    elif callback_query.data.startswith("user_prompt_create_npc_images_"):
        location_id = int(callback_query.data.removeprefix("user_prompt_create_npc_images_"))
        await callback_query.message.delete()
        await callback_query.bot.send_message(user_id, "Введите промпт для генерации изображения:")
        state['text_expect'] = f'image_prompt_npc_{location_id}'

    elif callback_query.data.startswith("description_create_locations_images_"):
        location_id = int(callback_query.data.removeprefix("description_create_locations_images_"))
        await process_location_generate_image(bot=callback_query.bot, user_id=user_id, location_id=location_id)

    elif callback_query.data.startswith("user_prompt_create_locations_images_"):
        location_id = int(callback_query.data.removeprefix("user_prompt_create_locations_images_"))
        await callback_query.message.delete()
        await callback_query.bot.send_message(user_id, "Введите промпт для генерации изображения:")
        state['text_expect'] = f'image_prompt_location_{location_id}'

    elif callback_query.data.startswith("save_image_location_"):
        location_id = int(callback_query.data.removeprefix("save_image_location_"))
        await save_location_image(location_id, callback_query.message.photo[-1].file_id)
        print('saved')
        await callback_query.message.delete()
        info = await get_location_info(location_id)
        keyboard = []
        if info.sub_locations is not None:
            for location in info.sub_locations:
                keyboard.append(
                    [InlineKeyboardButton(text=location.name, callback_data=f"location_{location.location_id}")])
        keyboard.append([InlineKeyboardButton(text="Посмотреть материалы",
                                              callback_data=f"show_materials_{location_id}")])
        keyboard.append([InlineKeyboardButton(text="Создать изображения",
                                              callback_data=f"create_locations_images_{location_id}")])
        keyboard.append([InlineKeyboardButton(text="Создать звуки окружения",
                                              callback_data=f"create_locations_sounds_{location_id}")])
        keyboard.append(
            [InlineKeyboardButton(text="Создать новую локацию",
                                  callback_data=f"create_location_{info.game_id}_{location_id}")])
        keyboard.append([InlineKeyboardButton(text="Удалить", callback_data=f"delete_location_{location_id}")])
        if info.parent_id is None:
            keyboard.append(
                [InlineKeyboardButton(text="← Назад", callback_data=f"list_locations_game_{info.game_id}")])
        else:
            keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"location_{info.parent_id}")])
        await callback_query.bot.send_message(user_id, f"Локация {info.name}\n{info.description}\n\nСуб-локации:",
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

    elif callback_query.data.startswith("save_image_npc_"):
        npc_id = int(callback_query.data.removeprefix("save_image_npc_"))
        await save_npc_image(npc_id, callback_query.message.photo[-1].file_id)
        print('saved')
        await callback_query.message.delete()
        npc_info = await get_npc_info(npc_id)
        keyboard = [[InlineKeyboardButton(text="Посмотреть материалы",
                                          callback_data=f"show_npc_materials_{npc_id}")],
                    [InlineKeyboardButton(text="Создать изображения",
                                          callback_data=f"images_npc_create_{npc_id}")],
                    [InlineKeyboardButton(text="Удалить", callback_data=f"delete_npc_{npc_id}")],
                    [InlineKeyboardButton(text="← Назад", callback_data=f"list_NPC_game_{npc_info.game_id}")]]
        await callback_query.bot.send_message(user_id,
                                              f"NPC {npc_info.name} для игры {npc_info.game_name}\n{npc_info.description}",
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

    elif callback_query.data.startswith("show_materials_"):
        location_id = int(callback_query.data.removeprefix("show_materials_"))
        ids = await get_location_image(location_id)
        if len(ids) == 0:
            await callback_query.bot.send_message(user_id, "Материалов пока нет")
        for i in range(0, int(len(ids) / 10) + 1):
            media = MediaGroupBuilder()
            for j in ids[(i * 10):((i + 1) * 10)]:
                media.add_photo(media=j)
            await callback_query.bot.send_media_group(user_id, media=media.build())

    elif callback_query.data.startswith("show_npc_materials_"):
        npc_id = int(callback_query.data.removeprefix("show_npc_materials_"))
        ids = await get_npc_image(npc_id)
        if len(ids) == 0:
            await callback_query.bot.send_message(user_id, "Материалов пока нет")
        for i in range(0, int(len(ids) / 10) + 1):
            media = MediaGroupBuilder()
            for j in ids[(i * 10):((i + 1) * 10)]:
                media.add_photo(media=j)
            await callback_query.bot.send_media_group(user_id, media=media.build())
    elif callback_query.data.startswith("create_locations_sounds_"):
        location_id = int(callback_query.data.removeprefix("create_locations_sounds_"))
        await callback_query.message.edit_text(f"Выберите способ генерации звука",
                                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                   [InlineKeyboardButton(text="Сгенерировать промпт на основе описаний",
                                                                         callback_data=f"description_create_locations_sounds_{location_id}")],
                                                   [InlineKeyboardButton(text="Мой промпт",
                                                                         callback_data=f"user_prompt_create_locations_sounds_{location_id}")]]))
    elif callback_query.data.startswith("user_prompt_create_locations_sounds_"):
        location_id = int(callback_query.data.removeprefix("user_prompt_create_locations_sounds_"))
        await callback_query.message.delete()
        await callback_query.bot.send_message(user_id, "Введите промпт для генерации звука:")
        state['text_expect'] = f'sound_prompt_location_{location_id}'

    elif callback_query.data.startswith("description_create_locations_sounds_"):
        location_id = int(callback_query.data.removeprefix("description_create_locations_sounds_"))
        await process_generate_audio(bot=callback_query.bot, user_id=user_id, location_id=location_id)


async def process_pdf_text_input(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]
    current_field = state['current_field']
    data_dict = state['data_dict']
    messages_to_delete = state['messages_to_delete']

    if data_dict is None:
        data_dict = dict()
    if messages_to_delete is None:
        messages_to_delete = []
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
            if current_field in main_fields:
                data_dict[current_field] = message.text
            elif current_field in characteristics_fields.keys():
                data_dict[characteristics_fields[current_field][0]] = message.text
                try:
                    data_dict[characteristics_fields[current_field][1]] = str(int((int(message.text) - 10) / 2))
                except:
                    pass

        state['current_field'] = None
        await message.delete()

        # Удаляем предыдущие сообщения
        for msg_id in messages_to_delete + form_messages:
            try:
                await message.bot.delete_message(message.from_user.id, msg_id)
            except:
                pass
        messages_to_delete.clear()
        form_messages.clear()

        # Путь к изображению
        image_path = "other/img/loading.jpg"

        # Создание объекта FSInputFile
        photo = FSInputFile(image_path)

        # Отправка изображения с текстом "Загрузка..."
        loading_msg = await message.bot.send_photo(
            chat_id=message.from_user.id,
            photo=photo,
            caption="Загрузка..."
        )

        # Добавление ID сообщения в список для удаления
        messages_to_delete.append(loading_msg.message_id)

        messages_to_delete.append(loading_msg.message_id)

        # Получаем путь к файлу из базы данных
        edited_file_path = await get_character_path(state['character_id'])
        if not edited_file_path:
            await message.bot.send_message(message.from_user.id, "Ошибка: файл не найден.")
            return

        # Обновляем PDF и создаем скриншот
        reader = PdfReader(edited_file_path)
        print(reader.get_form_text_fields())
        writer = PdfWriter()
        writer.set_need_appearances_writer()
        writer.clone_reader_document_root(reader)
        writer.set_need_appearances_writer()
        for i in range(len(reader.pages)):
            page = reader.pages[i]
            writer.add_page(page)
            writer.set_need_appearances_writer()
            writer.update_page_form_field_values(writer.pages[i], fields=data_dict)
        writer.set_need_appearances_writer()
        writer.write(edited_file_path)
        # with open(edited_file_path, 'wb') as output_pdf:
        #     writer.write(output_pdf)

        # Создаем скриншот страницы
        doc = fitz.open(edited_file_path)
        page = doc[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Отладочное сообщение для проверки скриншота
        print(f"Скриншот создан: {os.path.join('other', f'page_{user_id}.png')}")

        # Отправляем скриншот и кнопки навигации
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data=f"page3_{state['character_id']}"),
             InlineKeyboardButton(text="→", callback_data=f"page2_{state['character_id']}")],
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit_character_{state['character_id']}")],
            [InlineKeyboardButton(text="Экспортировать", callback_data=f"export_character_{state['character_id']}")],
            [InlineKeyboardButton(text="Отправить мастеру", callback_data=f"send_master_{state['character_id']}")],
            [InlineKeyboardButton(text="← Назад", callback_data=f"my_characters")]])

        # Редактируем сообщение "Загрузка..." с новым скриншотом
        await message.bot.edit_message_media(
            media=InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
            chat_id=message.from_user.id,
            message_id=loading_msg.message_id,
            reply_markup=keyboard
        )
        # await loading_msg.delete()
