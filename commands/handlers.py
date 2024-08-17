from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from ai.GPT import GPT4

router = Router()


class Generate(StatesGroup):
    text = State()


@router.message(F.text)
async def generate(message: Message, state: FSMContext):
    await  state.set_state(Generate.text)
    response = await GPT4(message.text)
    await message.answer(response.choices[0].message.content)
    await state.clear()


@router.message(Generate.text)
async def generate_error(message: Message):
    await message.answer('Загрузка...')

