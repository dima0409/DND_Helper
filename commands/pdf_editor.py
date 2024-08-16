from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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
from db.db_manager import add_user_character, update_user_character_name, delete_user_character, get_user_characters, \
    get_character_path


async def handle_docs(message: types.Message):
    user_id = message.from_user.id
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
    edited_file_path = os.path.join('other', 'pdf', 'characters_sheet.pdf')
    shutil.copyfile(file_path, edited_file_path)


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