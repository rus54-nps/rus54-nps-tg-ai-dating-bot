import logging
from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import os
from dotenv import load_dotenv  # Для загрузки переменных из .env

# Загружаем переменные окружения
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())
