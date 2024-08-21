import os

import openai
from dotenv import load_dotenv
import httpx
from openai import AsyncOpenAI

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'),
                     http_client=httpx.AsyncClient())


async def GPT4(question):
    try:
        response = await client.chat.completions.create(
            messages=[{"role": "user",
                       "content": str(question)}],
            model="gpt-4o-mini"
        )
        return response
    except openai.OpenAIError as e:
        print(f"An error occurred: {e}")
        return None
