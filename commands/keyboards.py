from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Режим игрока"), KeyboardButton(text="Режим мастера")]])

# Меню режима мастера
master_mode_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Создать новую игру"), KeyboardButton(text="Мои игры"),
     KeyboardButton(text="Начать сессию")]])

# Меню режима игрока
player_mode_keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                           keyboard=[[KeyboardButton(text="Присоединиться к сессии")]])

# Меню редактирования игры
game_edit_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Название", callback_data="edit_name"),
                      InlineKeyboardButton(text="Описание", callback_data="edit_description"),
                      InlineKeyboardButton(text="Локации", callback_data="edit_locations"),
                      InlineKeyboardButton(text="NPC", callback_data="edit_npc")]])

# Клавиатура подтверждения/отмены
confirm_cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_game"),
     InlineKeyboardButton(text="Отменить", callback_data="cancel_game")]])
