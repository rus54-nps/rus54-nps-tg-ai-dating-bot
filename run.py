# run.py
# Точка входа (запускает бота). Здесь ТОЛЬКО регистрация хендлеров и старт polling.

import logging
import asyncio
from aiogram import executor
from libs import dp

# Основные обработчики
from handlers import main_handlers, chat_handlers

# Опциональные хэндлеры
try:
    from handlers import purchase_handlers
except Exception:
    purchase_handlers = None

try:
    from handlers import admin_handlers
except Exception:
    admin_handlers = None

# 🕒 Напоминания (через 24 часа бездействия)
try:
    from services.reminder import reminder_loop
except Exception as e:
    reminder_loop = None
    print(f"⚠️ Reminder loop не подключён: {e}")


def register_all_handlers(dispatcher):
    """Регистрируем все обработчики, которые реализуют функцию register(dp)."""
    modules = (main_handlers, chat_handlers, purchase_handlers, admin_handlers)
    for mod in modules:
        if mod is None:
            continue
        if hasattr(mod, "register"):
            try:
                mod.register(dispatcher)
                logging.info(f"✅ Registered handlers from {mod.__name__}")
            except Exception as e:
                logging.exception(f"❌ Ошибка при регистрации handlers из {mod.__name__}: {e}")
        else:
            logging.info(f"ℹ️ Модуль {mod.__name__} не содержит register(dp) — пропускаем.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("🚀 Запуск бота — регистрация хендлеров...")
    register_all_handlers(dp)

    # ✅ Запуск фоновой задачи напоминаний
    if reminder_loop:
        loop = asyncio.get_event_loop()
        loop.create_task(reminder_loop())
        logging.info("🕒 Reminder loop запущен")

    logging.info("🤖 Start polling...")
    executor.start_polling(dp, skip_updates=True)
