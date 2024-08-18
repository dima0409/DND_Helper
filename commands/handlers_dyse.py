from aiogram import types
from aiogram.types import InputMediaPhoto, FSInputFile
from aiogram.types import Message

import random


async def send_d4_image(message: types.Message):
    roll_result = random.randint(1, 4)
    image_path = f'other/img/{roll_result}D4.png'
    try:
        photo = FSInputFile(image_path)
        caption = f'Вам выпала {roll_result}'
        await message.answer_photo(photo, caption=caption)
    except Exception as e:
        print(f"Error sending image: {e}")


async def send_d6_image(message: types.Message):
    roll_result = random.randint(1, 6)
    image_path = f'other/img/{roll_result}D6.png'
    try:
        photo = FSInputFile(image_path)
        caption = f'Вам выпала {roll_result}'
        await message.answer_photo(photo, caption=caption)
    except Exception as e:
        print(f"Error sending image: {e}")


async def send_d8_image(message: types.Message):
    roll_result = random.randint(1, 8)
    image_path = f'other/img/{roll_result}D8.png'
    try:
        photo = FSInputFile(image_path)
        caption = f'Вам выпала {roll_result}'
        await message.answer_photo(photo, caption=caption)
    except Exception as e:
        print(f"Error sending image: {e}")


async def send_d10_image(message: types.Message):
    roll_result = random.randint(0, 9)
    image_path = f'other/img/{roll_result}D10.png'
    try:
        photo = FSInputFile(image_path)
        caption = f'Вам выпала {roll_result}'
        await message.answer_photo(photo, caption=caption)
    except Exception as e:
        print(f"Error sending image: {e}")


async def send_d12_image(message: types.Message):
    roll_result = random.randint(1, 12)
    image_path = f'other/img/{roll_result}D12.png'
    try:
        photo = FSInputFile(image_path)
        caption = f'Вам выпала {roll_result}'
        await message.answer_photo(photo, caption=caption)
    except Exception as e:
        print(f"Error sending image: {e}")


async def send_d20_image(message: types.Message):
    roll_result = random.randint(1, 20)
    image_path = f'other/img/{roll_result}D20.png'
    try:
        photo = FSInputFile(image_path)
        caption = f'Вам выпала {roll_result}'
        await message.answer_photo(photo, caption=caption)
    except Exception as e:
        print(f"Error sending image: {e}")


async def send_d100_image(message: types.Message):
    roll_result = random.randint(0, 9)
    roll_result_str = f'{roll_result}0'
    image_path = f'other/img/{roll_result_str}D100.png'
    try:
        photo = FSInputFile(image_path)
        caption = f'Вам выпала {roll_result_str}'
        await message.answer_photo(photo, caption=caption)
    except Exception as e:
        print(f"Error sending image: {e}")
