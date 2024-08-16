import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import logging
import os
from dotenv import load_dotenv

from commands.info import process_help_command, process_start_command
from commands.pdf_editor import handle_docs, process_callback, process_pdf_field_input

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
"""dp.message.register(process_create_new_game, Command(commands='create_new_game'))
dp.message.register(process_my_games, Command(commands='my_games'))
dp.message.register(process_start_session, Command(commands='start_session'))
dp.message.register(process_create_session_command, Command(commands='create_session'))
dp.message.register(process_join_session_command, Command(commands='join_session'))"""
# dp.message.register(process_deletesession_command, Command(commands='deletesession'))
"""dp.message.register(process_answer_command, Command(commands='answer'))
"""# dp.message.register(process_leave_command, Command(commands='leave'))
"""dp.message.register(process_master_mode, Command(commands='master'))
dp.message.register(process_player_mode, Command(commands='player'))
dp.callback_query.register(process_confirm_game, lambda c: c.data == 'confirm_game')
dp.callback_query.register(process_cancel_game, lambda c: c.data == 'cancel_game')
dp.callback_query.register(process_edit_game, lambda c: c.data.startswith('edit_'))
dp.callback_query.register(join_callback_handler, lambda c: c.data and c.data.startswith('join_'))
dp.callback_query.register(confirm_join_callback_handler, lambda c: c.data and c.data.startswith('confirm_join_'))"""
# dp.callback_query.register(delete_session_callback_handler, lambda c: c.data and c.data.startswith('confirm_delete_'))
dp.callback_query.register(process_callback, lambda c: c.data)
dp.message.register(process_help_command, Command(commands='help'))
# dp.message.register(process_commands_command, Command(commands='commands'))
dp.message.register(handle_docs, Command(commands='edit'))
dp.message.register(process_pdf_field_input)


if __name__ == '__main__':
    try:
        logger.info("Starting bot")
        dp.run_polling(bot)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
