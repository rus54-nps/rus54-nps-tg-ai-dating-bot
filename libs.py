import logging
from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import os
from dotenv import load_dotenv

# Загружаем .env только если файл существует (чтобы не падало на Railway)
if os.path.exists(".env"):
    load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError(
        "BOT_TOKEN not found! "
        "Проверьте .env (для локальной работы) или переменные окружения на Railway."
    )

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())
