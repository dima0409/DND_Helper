import asyncio
import os
import time
from os import system

from ai.GPT import GPT4


async def get_audio_file(prompt: str, path="other/"):
    address = path + f"{time.time_ns()}.wav"
    command = f"wget http://oksnet.keenetic.pro:1488/{prompt.replace(' ', '%20')} -O '{address}'"
    system(command)
    return address


async def gen_stable_audio_prompt_by_descriptions(game_description: str, locations_description: str):
    return (await GPT4(f"""Я готовлюсь к игре в D&D, мне очень нужная твоя помощь, чтобы создать фоновые звуки. Пожалуйста преобразуй следующее описание игры и локации в промт для генерации изображения с помощью нейросети Stable audio:

Описание игры: {game_description}

Описание локации: {locations_description}

Пожалуйста сделай промт для Stable audio на английском языке четким и детализированным, он обязательно включать ключевые элементы и атмосферу описанной локации. При составлении промпта обязательно укажи жанр, геолокацию, десятилетие, желаемые инструменты, контекст (например "mau5trap label"), атмосферу и настроение.
Пожалуйста, напиши только сам промпт, он должен быть на английском языке""")).choices[0].message.content


if __name__ == "__main__":
    get_audio_file(input('prompt: '), "")
