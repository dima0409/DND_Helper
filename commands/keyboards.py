"""from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

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

@dp.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer("Добро пожаловать! Выберите режим:", reply_markup=main_menu_keyboard)

@dp.message(F.text == "Режим мастера")
async def master_mode(message: Message):
    await message.answer("Выберите действие:", reply_markup=master_mode_keyboard)

@dp.message(F.text == "Режим игрока")
async def player_mode(message: Message):
    await message.answer("Выберите действие:", reply_markup=player_mode_keyboard)

@dp.message(F.text == "Создать новую игру")
async def create_new_game(message: Message):
    await message.answer("Создание новой игры...")

@dp.message(F.text == "Мои игры")
async def my_games(message: Message):
    await message.answer("Ваши игры...")

@dp.message(F.text == "Начать сессию")
async def start_session(message: Message):
    await message.answer("Начало сессии...")

@dp.message(F.text == "Присоединиться к сессии")
async def join_session(message: Message):
    await message.answer("Присоединение к сессии...")

@dp.callback_query(F.data == 'edit_name')
async def process_edit_name(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Редактирование названия...", reply_markup=callback_query.message.reply_markup)

@dp.callback_query(F.data == 'edit_description')
async def process_edit_description(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Редактирование описания...", reply_markup=callback_query.message.reply_markup)

@dp.callback_query(F.data == 'edit_locations')
async def process_edit_locations(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Редактирование локаций...", reply_markup=callback_query.message.reply_markup)

@dp.callback_query(F.data == 'edit_npc')
async def process_edit_npc(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Редактирование NPC...", reply_markup=callback_query.message.reply_markup)

@dp.callback_query(F.data == 'confirm_game')
async def process_confirm_game(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Игра подтверждена.", reply_markup=callback_query.message.reply_markup)

@dp.callback_query(F.data == 'cancel_game')
async def process_cancel_game(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Игра отменена.", reply_markup=callback_query.message.reply_markup)"""