import logging
from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import os

# На Railway переменные окружения уже есть, .env не нужен
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError(
        "BOT_TOKEN не найден! Проверьте переменные окружения на Railway или .env для локальной работы."
    )

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())
