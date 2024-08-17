# DND_Helper
ДнД помощник

## Обзор
DND_Helper - это ваш верный помощник в ваших мирах D&D, он поможет вам найти себе компанию для игры, создать своего персонажа, или же подготовить материалы для лучшего погружения в вашу вселенную!

## Структура проекта

```structure
DND_Helper/
├── ai/
│   ├── __init__.py
│   ├── GPT.py
│   └── audio_gen.py
├── commands/
│   ├── __init__.py
│   ├── general.py
│   ├── handlers.py
│   ├── info.py
│   ├── pdf_editor.py
│   └──  session.py
├── db/
│   ├── data_models/
│   │   ├── __init__.py
│   │   ├── ChatacterModels.py
│   │   ├── GameModels.py
│   │   ├── LocationsModel.py
│   │   ├── NPCModel.py
│   │   └── SessionModel.py
│   ├── __init__.py
│   ├── db_manager.py
│   └── database.db
├── other/
│   ├── audio/
│   ├── img/
│   ├── img_gen/
│   └── characters_sheet.pdf
├── utils
│   ├── __init__.py
│   ├── list_utils.py
│   └── str_util.py
├── .env
├── .gitignore
├── LICENSE
├── main.py
└── README.md
```

## Преимущества проекта

- **Генерация картинок локаций** по описанию с помощью GPT-4o mini
- **Создание звуковых эффектов** с помощью Stable Audio.
- **Связь игроков** с мастером через сессии
- **Помощь игрокам в заполнении анкеты** персонажа и создания PDF-файла.

## Инструкция по запуску

### 1. Скачивание аудио модели

Скачайте [аудио модель](https://huggingface.co/stabilityai/stable-audio-open-1.0)

### 2. Подготовка окружения

### Создание файлов среды 

Создайте файл среды `.env` в корне директории `DND_Helper/` и заполните его данными о апи ключах:
```plaintext
BOT_TOKEN = API TELEGRAM
OPENAI_API_KEY= API GPT
```

### 3. Запуск

Скачайте все нужные библиотеки и потом запустите `main.py`

```
pip install aiogram
pip install python-dotenv
pip install PyPDF2
pip install pillow
pip install PyMuPDF
pip install openai
pip install asyncio
pip install aiosqlite
pip install httpx
```
## Используемые технологии

- **Модели и аналитика**: Использование языковой модели GPT-4o Mini и так же звуковой Stable Audio 1.0

## Заключение

DND_Helper — это ваш незаменимый спутник в мире Dungeons & Dragons. С его помощью вы сможете легко найти компанию для игры, создать уникального персонажа и подготовить материалы для полного погружения в вашу вселенную. Давайте вместе сделаем ваши приключения в D&D еще более увлекательными и незабываемыми!