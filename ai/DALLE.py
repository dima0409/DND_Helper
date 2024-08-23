import asyncio

from openai import OpenAI
from ai.GPT import *

client = OpenAI()


async def generate_images(prompt: str):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return list(map(lambda x: x.url, response.data))[0]


async def gen_dalle_prompt_by_descriptions(game_description: str, locations_description: str):
    return (await GPT4(f"""Я готовлюсь к игре в D&D, мне очень нужная твоя помощь, чтобы создать изображения. Пожалуйста преобразуй следующее описание игры и локации в промт для генерации изображения с помощью DALL-E 3:

Описание игры: {game_description}

Описание локации: {locations_description}

Пожалуйста сделай промт для DALL-E 3 четким и детализированным, он обязательно включать ключевые элементы и атмосферу описанной локации. Например, если в описании упоминаются горы, деревья и озеро, промт должен включать эти элементы и описывать их внешний вид и расположение. Если в описании упоминается время суток или погодные условия, это также должно быть включено в промт.
Пожалуйста, напиши только сам промпт""")).choices[0].message.content

async def gen_dalle_NPC_prompt_by_descriptions(game_description: str, npc_description: str):
    return (await GPT4(f"""Я готовлюсь к игре в D&D, мне очень нужная твоя помощь, чтобы создать изображения. Пожалуйста преобразуй следующее описание игры и персонажа в промт для генерации изображения с помощью DALL-E 3:

Описание игры: {game_description}

Описание персонажа: {npc_description}

Пожалуйста сделай промт для DALL-E 3 четким и детализированным, он обязательно включать ключевые элементы описанного персонажа.
Пожалуйста, напиши только сам промпт""")).choices[0].message.content
