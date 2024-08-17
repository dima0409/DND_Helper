import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from commands.info import process_help_command, process_start_command
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
dp.message.register(process_text_input)  # комент если нужен гпт
dp.include_router(router)

dp.callback_query.register(process_callback, lambda c: c.data)

if __name__ == '__main__':
    try:
        logger.info("Starting bot")
        dp.run_polling(bot)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
