from collections import defaultdict

user_states = defaultdict(lambda: defaultdict(lambda: None))
form_messages = []


async def provide_error(bot, user_id):
    await bot.send_message(user_id, f"Извините произошла ошибка, уже чиним!")
