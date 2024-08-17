from aiogram.types import Message
from db.db_manager import is_user_signup
from commands.keyboards import main_menu_keyboard

async def process_start_command(message: Message):
    await message.answer(
        text='Привет!\nНапиши /help',
        reply_markup=main_menu_keyboard)


# Этот хэндлер будет срабатывать на команду "/help"
async def process_help_command(message: Message):
    await message.answer(
        "Доступные команды:`/start`, `/create`, `/join`, `/help`, `/commands`, `/deletesession`, `/answer <текст>`, `/leave`",
        parse_mode = 'Markdown'
    )
