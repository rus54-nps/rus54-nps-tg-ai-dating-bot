import asyncio
import time
import random
from libs import bot
from services.storage import get_last_active, get_all_active_users
from handlers.chat_handlers import user_states, send_human_like_message

# Проверка каждые 30 секунд (часто, чтобы быстрее реагировать)
CHECK_INTERVAL = 30  # секунд

# Интервал напоминания (в минутах)
REMINDER_MIN_MINUTES = 1200  # 20 часов
REMINDER_MAX_MINUTES = 1800  # 30 часов

# Фразы по умолчанию (если не указаны в YAML)
default_reminders = [
    "Ты куда пропал? 😊",
    "Я уже соскучилась ❤️",
    "Давно не писали друг другу 😅",
    "Хочу услышать тебя снова 💫",
    "Надеюсь, у тебя всё хорошо 🌷",
]

# Храним для каждого пользователя персональный "таймер"
_user_reminder_target = {}

def get_random_reminder_delay():
    """Возвращает случайную задержку в секундах"""
    minutes = random.uniform(REMINDER_MIN_MINUTES, REMINDER_MAX_MINUTES)
    return minutes * 60


async def reminder_loop():
    print("🕒 Reminder loop запущен (1–2 минуты для теста)...")
    while True:
        now = time.time()

        for user_id in get_all_active_users():
            last = get_last_active(user_id)

            # Если нет активной девушки — пропускаем
            if user_id not in user_states:
                continue

            girl = user_states[user_id]
            girl_name = girl.get("name", "Она")

            # Если для пользователя ещё не создан таймер — создаём
            if user_id not in _user_reminder_target:
                _user_reminder_target[user_id] = last + get_random_reminder_delay()

            # Проверяем, пора ли отправить сообщение
            target_time = _user_reminder_target[user_id]
            if now >= target_time:
                # Получаем индивидуальные фразы, если заданы в YAML
                girl_reminders = girl.get("reminders", default_reminders)
                phrase = random.choice(girl_reminders)

                try:
                    await send_human_like_message(bot, user_id, phrase)
                    print(f"📨 Напоминание отправлено пользователю {user_id} от {girl_name}: {phrase}")
                except Exception as e:
                    print(f"⚠️ Ошибка при отправке напоминания {user_id}: {e}")

                # Обновляем время — создаём новый "рандомный таймер"
                _user_reminder_target[user_id] = now + get_random_reminder_delay()

        await asyncio.sleep(CHECK_INTERVAL)
