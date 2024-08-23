from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from db.data_models.LocationsModel import GameLocation

# Главное меню
player_menu_keyboard_button = KeyboardButton(
    text='Режим игрока'
)

master_menu_keyboard_button = KeyboardButton(
    text='Режим мастера'
)

# Меню
main_menu_keyboard = ReplyKeyboardMarkup(keyboard=[[master_menu_keyboard_button, player_menu_keyboard_button]],
                                         resize_keyboard=True)

# Меню режима мастера
master_mode_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Мои игры')]], resize_keyboard=True
)

# Меню режима игрока
player_mode_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Мои игры")],
              [KeyboardButton(text="Мои персонажи")]], resize_keyboard=True)

master_session_unlocked_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Начать игру (заблокировать подключения)")],
              [KeyboardButton(text="Остановить сессию")], [KeyboardButton(text="Список игроков")]],
    resize_keyboard=True)

master_session_locked_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Остановить игру (разблокировать подключения)")],
              [KeyboardButton(text="Остановить сессию")], [KeyboardButton(text="Список игроков")]],
    resize_keyboard=True)


def make_game_keyboard(game_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать сессию", callback_data=f"start_session_{game_id}")],
        [InlineKeyboardButton(text="Материалы", callback_data=f"materials_{game_id}")],
        [InlineKeyboardButton(text="Изменить название", callback_data=f"change_game_name_{game_id}")],
        [InlineKeyboardButton(text="Изменить описание", callback_data=f"change_game_description_{game_id}")],
        [InlineKeyboardButton(text="Удалить", callback_data=f"delete_game_{game_id}")]
    ])


def location_keyboard(info: GameLocation):
    keyboard = []
    if info.sub_locations is not None:
        for location in info.sub_locations:
            keyboard.append(
                [InlineKeyboardButton(text=location.name, callback_data=f"location_{location.location_id}")])
    keyboard.append([InlineKeyboardButton(text="Посмотреть материалы",
                                          callback_data=f"show_materials_{info.location_id}")])
    keyboard.append([InlineKeyboardButton(text="Создать изображения",
                                          callback_data=f"create_locations_images_{info.location_id}")])
    keyboard.append([InlineKeyboardButton(text="Создать звуки окружения",
                                          callback_data=f"create_locations_sounds_{info.location_id}")])
    keyboard.append(
        [InlineKeyboardButton(text="Создать новую локацию",
                              callback_data=f"create_location_{info.game_id}_{info.location_id}")])
    keyboard.append([InlineKeyboardButton(text="Удалить", callback_data=f"delete_location_{info.location_id}")])
    if info.parent_id is None:
        keyboard.append(
            [InlineKeyboardButton(text="← Назад", callback_data=f"list_locations_game_{info.game_id}")])
    else:
        keyboard.append([InlineKeyboardButton(text="← Назад", callback_data=f"location_{info.parent_id}")])
    return keyboard
