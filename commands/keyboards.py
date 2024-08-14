"""from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.add(KeyboardButton("Режим игрока"), KeyboardButton("Режим мастера"))

# Меню режима мастера
master_mode_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
master_mode_keyboard.add(KeyboardButton("Создать новую игру"), KeyboardButton("Мои игры"), KeyboardButton("Начать сессию"))

# Меню режима игрока
player_mode_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
player_mode_keyboard.add(KeyboardButton("Присоединиться к сессии"))

# Меню редактирования игры
game_edit_keyboard = InlineKeyboardMarkup()
game_edit_keyboard.add(InlineKeyboardButton("Название", callback_data="edit_name"))
game_edit_keyboard.add(InlineKeyboardButton("Описание", callback_data="edit_description"))
game_edit_keyboard.add(InlineKeyboardButton("Локации", callback_data="edit_locations"))
game_edit_keyboard.add(InlineKeyboardButton("NPC", callback_data="edit_npc"))

# Клавиатура подтверждения/отмены
confirm_cancel_keyboard = InlineKeyboardMarkup()
confirm_cancel_keyboard.add(InlineKeyboardButton("Подтвердить", callback_data="confirm_game"))
confirm_cancel_keyboard.add(InlineKeyboardButton("Отменить", callback_data="cancel_game"))
"""