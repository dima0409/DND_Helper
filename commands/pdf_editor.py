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


async def process_pdf_callback(callback_query: types.CallbackQuery):
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

    elif callback_query.data.startswith("export_character_"):
        character_id = int(callback_query.data.removeprefix("export_character_"))
        edited_file_path = await get_character_path(character_id)
        if not edited_file_path:
            await callback_query.bot.send_message(callback_query.from_user.id, "Ошибка: файл не найден.")
            return

        await callback_query.bot.send_document(callback_query.from_user.id, FSInputFile(edited_file_path))




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
