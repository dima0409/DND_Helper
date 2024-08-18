import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from commands.info import process_help_command, process_start_command
from commands.handlers_dyse import send_d4_image, send_d6_image, send_d8_image, send_d10_image, send_d12_image, \
    send_d20_image, send_d100_image
from commands.pdf_editor import handle_docs, process_callback
from commands.text_commands import process_text_input  # комент если нужен гпт
from commands.handlers import router

import os
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем хэндлеры
dp.message.register(process_start_command, Command(commands='start'))
dp.message.register(process_help_command, Command(commands='help'))
dp.message.register(handle_docs, Command(commands='edit'))
dp.message.register(send_d4_image, Command(commands='d4'))
dp.message.register(send_d6_image, Command(commands='d6'))
dp.message.register(send_d8_image, Command(commands='d8'))
dp.message.register(send_d10_image, Command(commands='d10'))
dp.message.register(send_d12_image, Command(commands='d12'))
dp.message.register(send_d20_image, Command(commands='d20'))
dp.message.register(send_d100_image, Command(commands='d100'))
dp.message.register(process_text_input)  # Ниже не ставить
dp.include_router(router)  # ГПТ

dp.callback_query.register(process_callback, lambda c: c.data)

if __name__ == '__main__':
    try:
        logger.info("Starting bot")
        dp.run_polling(bot)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
