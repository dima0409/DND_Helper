import asyncio

from openai import OpenAI
from ai.GPT import *

client = OpenAI()


async def generate_images(prompt: str):
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=4,
    )

    return list(map(lambda x: x.url, response.data))


async def generate_images_with_gpt_prompt(prompt: str):
    return await generate_images((await GPT4(prompt)).choices[0].message.content)


def gen_prompt_by_descriptions(game_description: str, locations_description: str):
    f"""Я готовлюсь к игре в D&D, мне очень нужная твоя помощь, чтобы создать изображения. Пожалуйста преобразуй следующее описание игры и локации в промт для генерации изображения с помощью DALL-E 3:

Описание игры: {game_description}

Описание локации: {locations_description}

Пожалуйста сделай промт для DALL-E 3 четким и детализированным, он обязательно включать ключевые элементы и атмосферу описанной локации. Например, если в описании упоминаются горы, деревья и озеро, промт должен включать эти элементы и описывать их внешний вид и расположение. Если в описании упоминается время суток или погодные условия, это также должно быть включено в промт.
Пожалуйста, напиши только сам промпт"""


if __name__ == "__main__":
    print(asyncio.run(
        generate_images_with_gpt_prompt("Подготовь промпт для DALL-E-3, чтобы он нарисовал красивого рыжего кота")))
