from aiogram.types import Message
#from db.db_manager import get_role

async def process_start_command(message: Message):
    await message.answer('Привет!\nНапиши /help')


# Этот хэндлер будет срабатывать на команду "/help"
async def process_help_command(message: Message):
    await message.answer(
        "Доступные команды:`/start`, `/create`, `/join`, `/help`, `/commands`, `/deletesession`, `/answer <текст>`, `/leave`",
        parse_mode = 'Markdown'
    )


# async def process_commands_command(message: Message):
    user_id = message.from_user.id
    # role = await get_role(user_id)
    # if role == 'master':
    #     await message.answer("Доступные команды для мастера: /startgame, /endgame, /deletesession")
    # else:
    #     await message.answer("У вас нет прав для выполнения этой команды.")
