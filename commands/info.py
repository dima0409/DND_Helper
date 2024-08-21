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
        await message.answer(text=f'Привет 👋, {name}!\nНапиши /help', reply_markup=main_menu_keyboard)
    else:
        state['text_expect'] = 'User_name'
        await message.answer(text=f'Привет 👋\nДавай знакомиться! Как тебя зовут?', reply_markup=None)


# Этот хэндлер будет срабатывать на команду "/help"
async def process_help_command(message: Message):
    await message.answer(
        'Я ваш незаменимый спутник в мире Dungeons & Dragons.'
        ' С моей помощью вы сможете легко найти компанию для игры, создать уникального персонажа и подготовить материалы для полного погружения в вашу вселенную.'
        ' Давайте вместе сделаем ваши приключения в D&D еще более увлекательными и незабываемыми.\n'
        '**Контакты:** `dnd_helper_help@gmail.com`\n'
        'Следите за разработкой и новостями в [нашем канале](https://t.me/DevDnDMastersHelp)!',
        parse_mode='Markdown'
    )
