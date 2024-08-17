from aiogram.types import Message
from db.db_manager import get_user_name
from commands.general import user_states
from commands.keyboards import main_menu_keyboard


async def process_start_command(message: Message):
    user_id = message.from_user.id
    state = user_states[user_id]
    name = await get_user_name(message.from_user.id)
    if name:
        state['user_name'] = name
        await message.answer(text=f'Привет 👋, {name}!\nНапиши /info', reply_markup=main_menu_keyboard)
    else:
        state['text_expect'] = 'User_name'
        await message.answer(text=f'Привет 👋\nДавай знакомиться! Как тебя зовут?', reply_markup=main_menu_keyboard)


# Этот хэндлер будет срабатывать на команду "/help"
async def process_help_command(message: Message):
    await message.answer(
        "Доступные команды:`/start`, `/create`, `/join`, `/help`, `/commands`, `/deletesession`, `/answer <текст>`, `/leave`",
        parse_mode='Markdown'
    )
