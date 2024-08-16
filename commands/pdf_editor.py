from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject
from PIL import Image
from commands.general import user_states
import fitz  # PyMuPDF
import os


def set_need_appearances_writer(writer):
    try:
        catalog = writer._root_object
        if "/AcroForm" not in catalog:
            writer._root_object.update({
                NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)
            })
        need_appearances = NameObject("/NeedAppearances")
        writer._root_object["/AcroForm"][need_appearances] = BooleanObject(True)
        return writer
    except Exception as e:
        print('set_need_appearances_writer() catch : ', repr(e))
        return writer


async def handle_docs(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {'current_page': 0, 'current_field': None, 'data_dict': {}, 'messages_to_delete': []}

    # Загружаем анкету персонажа D&D из папки other
    file_path = os.path.join('other', 'character_sheet.pdf')

    # Создаем скриншот страницы
    doc = fitz.open(file_path)
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

    if callback_query.data.startswith("page_"):
        current_page = int(callback_query.data.split("_")[1])
        state['current_page'] = current_page

        # Создаем скриншот страницы
        doc = fitz.open(os.path.join('other', 'character_sheet.pdf'))
        page = doc[current_page]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Определяем поля для текущей страницы
        if current_page == 0:
            fields = ['CharacterName', 'ClassLevel', 'Background', 'PlayerName', 'Race', 'Alignment']
        elif current_page == 1:
            fields = ['ExperiencePoints', 'Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
        else:
            fields = ['OtherField1', 'OtherField2', 'OtherField3']  # Добавьте поля для других страниц

        # Отправляем скриншот и кнопки навигации
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Выбрать поле", callback_data="select_field")
        keyboard.button(text="Сохранить", callback_data="save")
        keyboard.button(text="Отмена", callback_data="cancel")
        keyboard.button(text="1", callback_data="page_0")
        keyboard.button(text="2", callback_data="page_1")
        keyboard.button(text="3", callback_data="page_2")
        keyboard.adjust(3, 3)

        new_media = InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png')))
        await callback_query.message.edit_media(new_media, reply_markup=keyboard.as_markup())

    elif callback_query.data == "select_field":
        keyboard = InlineKeyboardBuilder()
        if current_page == 0:
            fields = ['CharacterName', 'ClassLevel', 'Background', 'PlayerName', 'Race', 'Alignment']
        elif current_page == 1:
            fields = ['ExperiencePoints', 'Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
        else:
            fields = ['OtherField1', 'OtherField2', 'OtherField3']  # Добавить

        for field in fields:
            keyboard.button(text=field, callback_data=f"field_{field}")
        keyboard.button(text="Назад", callback_data="back")
        keyboard.adjust(1)

        await callback_query.message.edit_reply_markup(reply_markup=keyboard.as_markup())

    elif callback_query.data.startswith("field_"):
        current_field = callback_query.data.split("_")[1]
        state['current_field'] = current_field
        state['text_expect'] = "PDF"
        msg = await callback_query.bot.send_message(callback_query.from_user.id,
                                                    f"Введите значение для поля {current_field}:")
        messages_to_delete.append(msg.message_id)

    elif callback_query.data == "confirm":
        # Открываем PDF и редактируем его
        reader = PdfReader(os.path.join('other', 'character_sheet.pdf'))
        writer = PdfWriter()
        await set_need_appearances_writer(writer)

        for i in range(len(reader.pages)):
            page = reader.pages[i]
            writer.update_page_form_field_values(page, fields=data_dict)
            writer.add_page(page)

        with open(os.path.join('other', f'edited_{user_id}.pdf'), 'wb') as output_pdf:
            writer.write(output_pdf)

        # Создаем скриншот страницы
        doc = fitz.open(os.path.join('other', f'edited_{user_id}.pdf'))
        page = doc[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Отправляем сообщение с кнопками "Сохранить" и "Отмена"
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Сохранить", callback_data="save")
        keyboard.button(text="Отмена", callback_data="cancel")
        keyboard.adjust(1)

        await callback_query.bot.send_message(callback_query.from_user.id, "Просмотр редактированной PDF:",
                                              reply_markup=keyboard.as_markup())
        await callback_query.bot.send_document(callback_query.from_user.id,
                                               FSInputFile(os.path.join('other', f'edited_{user_id}.pdf')))

    elif callback_query.data == "save":
        # Создаем новый PDF файл с ID пользователя
        reader = PdfReader(os.path.join('other', 'character_sheet.pdf'))
        writer = PdfWriter()
        set_need_appearances_writer(writer)

        for i in range(len(reader.pages)):
            page = reader.pages[i]
            writer.update_page_form_field_values(page, fields=data_dict)
            writer.add_page(page)

        new_pdf_path = os.path.join('other', f'final_{user_id}.pdf')
        with open(new_pdf_path, 'wb') as output_pdf:
            writer.write(output_pdf)

        # Отправляем новый PDF файл пользователю
        await callback_query.bot.send_document(callback_query.from_user.id, FSInputFile(new_pdf_path))
        await callback_query.bot.send_message(callback_query.from_user.id, "Изменения сохранены.")

        # Удаляем предыдущие сообщения
        for msg_id in messages_to_delete:
            await callback_query.bot.delete_message(callback_query.from_user.id, msg_id)
        messages_to_delete.clear()

    elif callback_query.data == "cancel":
        await callback_query.bot.send_message(callback_query.from_user.id, "Изменения отменены.")

        # Удаляем предыдущие сообщения
        for msg_id in messages_to_delete:
            await callback_query.bot.delete_message(callback_query.from_user.id, msg_id)
        messages_to_delete.clear()

    elif callback_query.data == "back":
        # Возвращаемся к предыдущему состоянию
        current_page = state['current_page']
        current_field = None
        data_dict = state['data_dict']
        messages_to_delete = state['messages_to_delete']

        # Создаем скриншот страницы
        doc = fitz.open(os.path.join('other', 'character_sheet.pdf'))
        page = doc[current_page]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(os.path.join('other', f'page_{user_id}.png'))

        # Определяем поля для текущей страницы
        if current_page == 0:
            fields = ['CharacterName', 'ClassLevel', 'Background', 'PlayerName', 'Race', 'Alignment']
        elif current_page == 1:
            fields = ['ExperiencePoints', 'Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
        else:
            fields = ['OtherField1', 'OtherField2', 'OtherField3']  # Добавьте поля для других страниц

        # Отправляем скриншот и кнопки навигации
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Выбрать поле", callback_data="select_field")
        keyboard.button(text="Сохранить", callback_data="save")
        keyboard.button(text="Отмена", callback_data="cancel")
        keyboard.button(text="1", callback_data="page_0")
        keyboard.button(text="2", callback_data="page_1")
        keyboard.button(text="3", callback_data="page_2")
        keyboard.adjust(3, 3)

        await callback_query.message.edit_media(
            InputMediaPhoto(media=FSInputFile(os.path.join('other', f'page_{user_id}.png'))),
            reply_markup=keyboard.as_markup()
        )


async def process_pdf_field_input(message: types.Message):
    user_id = message.from_user.id

    state = user_states[user_id]

    current_field = state['current_field']

    data_dict = state['data_dict']

    messages_to_delete = state['messages_to_delete']

    if current_field:
        data_dict[current_field] = message.text

        state['current_field'] = None

        await message.delete()

        # Сохраняем значение и отправляем сообщение
        msg = await message.bot.send_message(message.from_user.id, "Значение сохранено. Выберите следующее действие.")
        messages_to_delete.append(msg.message_id)

        # Обновляем PDF и создаем скриншот
        reader = PdfReader(os.path.join('other', 'character_sheet.pdf'))
        writer = PdfWriter()
        set_need_appearances_writer(writer)

        for i in range(len(reader.pages)):
            page = reader.pages[i]
            writer.update_page_form_field_values(page, fields=data_dict)
            writer.add_page(page)

        with open(os.path.join('other', f'edited_{user_id}.pdf'), 'wb') as output_pdf:
            writer.write(output_pdf)

        # Создаем скриншот страницы
        doc = fitz.open(os.path.join('other', f'edited_{user_id}.pdf'))
        page = doc[state['current_page']]
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

        await message.bot.send_photo(message.from_user.id, FSInputFile(os.path.join('other', f'page_{user_id}.png')),
                                     reply_markup=keyboard.as_markup())
