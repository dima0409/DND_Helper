import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from commands.info import process_help_command, process_start_command
# from commands.session import process_create_command, process_join_command, process_deletesession_command, process_answer_command, process_leave_command, join_callback_handler, confirm_join_callback_handler, delete_session_callback_handler
from commands.pdf_editor import handle_docs, process_callback, process_text_input

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
# dp.message.register(process_create_command, Command(commands='create'))
# dp.message.register(process_join_command, Command(commands='join'))
dp.message.register(process_help_command, Command(commands='help'))
# dp.message.register(process_commands_command, Command(commands='commands'))
# dp.message.register(process_deletesession_command, Command(commands='deletesession'))
# dp.message.register(process_answer_command, Command(commands='answer'))
# dp.message.register(process_leave_command, Command(commands='leave'))
dp.message.register(handle_docs, Command(commands='edit'))
dp.message.register(process_text_input)
# dp.callback_query.register(join_callback_handler, lambda c: c.data and c.data.startswith('join_'))
# dp.callback_query.register(confirm_join_callback_handler, lambda c: c.data and c.data.startswith('confirm_join_'))
# dp.callback_query.register(delete_session_callback_handler, lambda c: c.data and c.data.startswith('confirm_delete_'))
dp.callback_query.register(process_callback, lambda c: c.data)

if __name__ == '__main__':
    try:
        logger.info("Starting bot")
        dp.run_polling(bot)
    except Exception as e:
        logger.error(f"Error occurred: {e}")