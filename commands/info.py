from aiogram.types import Message
from db.db_manager import is_user_signup

async def process_start_command(message: Message):
    await message.answer('Привет!\nНапиши /help')


# Этот хэндлер будет срабатывать на команду "/help"
async def process_help_command(message: Message):
    await message.answer(
        "Доступные команды:`/start`, `/create`, `/join`, `/help`, `/commands`, `/deletesession`, `/answer <текст>`, `/leave`",
        parse_mode = 'Markdown'
    )
