import os
import yaml
import requests
import asyncio
import random
import re
import pytz
from aiogram import Bot
from datetime import datetime
from aiogram import types, Dispatcher
from keyboards import get_girl_selection_keyboard
from dotenv import load_dotenv
from services.storage import add_message, get_dialog, clear_dialog
from services.moderation import check_message
from services.greetings import get_greeting
from datetime import datetime, timedelta

# Лимит сообщений в день на одного пользователя
DAILY_MESSAGE_LIMIT = 15
# Храним количество сообщений и дату последнего обновления
_user_daily_stats = {}
user_profiles = {}

limit_reached_phrases = [
    "Кажется, мне нельзя писать тебе больше сегодня... 😔 Я бы с радостью поболтала ещё, но правила есть правила ❤️ Буду ждать тебя завтра… или, может, ты найдёшь способ увидеть меня раньше 😉",
    "Эй, ты сегодня уже весь мой лимит сообщений исчерпал 😅 А я ведь только разогрелась... Не заставляй меня скучать до завтра 💫 (хотя... может, у тебя есть способ продлить наше общение 😉)",
    "Похоже, сегодня мне больше нельзя писать 😔 Но я очень жду нашей следующей беседы ❤️ Иногда хочется, чтобы лимитов просто не существовало... 😌",
    "Ты уже сегодня так много со мной говорил, что мне запретили писать 😅 Но я же хочу ещё... может, ты что-то придумаешь? 😉",
]

async def send_human_like_message(bot, chat_id: int, text: str, instant_first: bool = False):
    """
    Имитация "человеческой" отправки:
    - показывает 'typing' всё время ожидания (обновляет chat_action каждые few seconds),
    - рассчитывает задержку по длине текста,
    - дробит текст на параграфы и отправляет по очереди.
    Параметры:
      bot - объект aiogram.Bot (или libs.bot)
      chat_id - id чата (int)
      text - текст сообщения (можно с несколькими абзацами)
      instant_first - если True, первый абзац отправляется сразу (без typing)
    """
    # Разбиваем на параграфы (сохраняем пустые строки)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # Параметры задержки (тонкая настройка)
    per_char = 0.02        # секунды на символ (регулируй)
    min_delay = 0.6        # минимальная задержка перед отправкой параграфа
    max_delay = 4.5        # максимальная задержка перед отправкой параграфа
    chat_action_interval = 4.0  # как часто обновлять 'typing' (сек)

    for i, para in enumerate(paragraphs):
        # Если first paragraph должен уйти мгновенно
        if instant_first and i == 0:
            await bot.send_message(chat_id, para)
            continue

        # Рассчитываем нужную задержку для текущего параграфа
        computed = len(para) * per_char
        delay = max(min_delay, min(max_delay, computed))

        # Показываем 'typing' и обновляем это действие каждые chat_action_interval сек
        # в течение delay секунд.
        # Отправляем одно действие сразу, затем цикл sleep+send_chat_action
        try:
            await bot.send_chat_action(chat_id, types.ChatActions.TYPING)
        except Exception:
            # в редких случаях send_chat_action может падать — безопасно игнорируем
            pass

        # обновляем индикатор периодически
        elapsed = 0.0
        tick = chat_action_interval
        while elapsed < delay:
            # спим меньший кусок, чтобы можно было прервать, если нужно
            sleep_time = min(tick, delay - elapsed)
            await asyncio.sleep(sleep_time)
            elapsed += sleep_time
            # обновляем typing (если ещё не закончилось время)
            if elapsed < delay:
                try:
                    await bot.send_chat_action(chat_id, types.ChatActions.TYPING)
                except Exception:
                    pass

        # Отправляем параграф
        try:
            await bot.send_message(chat_id, para)
        except Exception as e:
            # Если отправка упала (например, блокировка), логируем и выходим
            print(f"⚠️ Ошибка при отправке сообщения: {e}")
            return


def filter_prohibited(text: str) -> bool:
    """
    Проверяет сообщение на наличие запрещённых выражений.
    Возвращает True, если в тексте найдено что-то неуместное.
    """
    prohibited_words = [
        "секс", "эрот", "порно", "голая", "сиськи", "член", "минет",
        "видео 18", "nsfw", "sex", "porn"
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in prohibited_words)

def set_user_name(user_id, name: str):
    if user_id not in _user_profiles:
        _user_profiles[user_id] = {}
    _user_profiles[user_id]["name"] = name

def get_user_name(user_id) -> str | None:
    return _user_profiles.get(user_id, {}).get("name")

# Загружаем .env
load_dotenv()

OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

user_states = {}
_user_profiles = {}

girl_name_map = {
    "софия": "sofia",
    "вика": "vika"
}

def load_girl_data(girl_name):
    girl_name = girl_name.strip().lower()
    file_name = girl_name_map.get(girl_name, girl_name)
    file_path = os.path.join('girls', f'{file_name}.yaml')

    if not os.path.exists(file_path):
        print(f"Ошибка: файл {file_path} не найден!")
        return None

    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

# --------------- НОВЫЕ ХЕЛПЕРЫ -----------------

def extract_user_name(user_text: str) -> str | None:
    """
    Более точная проверка имени:
    - 'Меня зовут Имя'
    - 'Я Имя' (в начале строки)
    - 'Моё имя Имя'
    """
    user_text = user_text.strip()
    # варианты: "Меня зовут Серёжа", "Я Серёжа", "Моё имя Серёжа"
    patterns = [
        r"^(?:меня зовут|меня зовут:)\s+([А-ЯЁ][а-яё]+)$",
        r"^(?:я)\s+([А-ЯЁ][а-яё]+)$",
        r"^(?:моё имя|моё имя:)\s+([А-ЯЁ][а-яё]+)$",
    ]
    for pat in patterns:
        m = re.search(pat, user_text, re.IGNORECASE)
        if m:
            return m.group(1).capitalize()
    return None

def get_local_time_str(timezone_str: str = "UTC"):
    """
    Возвращает (HH:MM, period) где period — 'утро','день','вечер','ночь'.
    """
    try:
        tz = pytz.timezone(timezone_str)
    except Exception:
        tz = pytz.UTC
    now = datetime.now(tz)
    time_str = now.strftime("%H:%M")
    hour = now.hour
    if 5 <= hour < 12:
        period = "утро"
    elif 12 <= hour < 18:
        period = "день"
    elif 18 <= hour < 23:
        period = "вечер"
    else:
        period = "ночь"
    return time_str, period

# --------------- МОДЕРНИЗИРОВАННЫЙ PROMPT -----------------
def get_ai_response(prompt: str, system_prompt: str = None):
    """
    system_prompt должен быть на английском (persona + инструкции).
    Базовая инструкция — на английском, модель просят отвечать по-русски.
    """
    try:
        base_system_prompt = (
            "You are a Russian-speaking female persona who chats in Telegram style. "
            "Always respond in Russian using informal 'ты'. Keep messages short, natural, friendly and grammatically correct. "
            "Do NOT invent life events (work, lectures, diploma, sessions) or durations unless explicitly asked. "
            "If the system prompt includes an exact local time for the character, use that exact time when asked and do not add invented comments. "
            "Do not re-introduce yourself if you already greeted the user. "
            "Avoid nonsensical numeric phrases like 'hours two-two'."
        )

        full_prompt = base_system_prompt + ("\n\n" + system_prompt if system_prompt else "")

        url = f"{OLLAMA_API}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        reply = data.get("message", {}).get("content", "...")

        # минимальная пост-обработка: убираем случайные оставшиеся английские слова
        cleanup = {
            "lately": "",
            "yesterday": "",
            "indeed": "",
            "however": "",
            "perhaps": "",
        }
        for bad, fix in cleanup.items():
            reply = reply.replace(bad, fix)

        # небольшие безопасные правки (если модель выдала "Очень приятно, Сейчас!" и т.п.)
        reply = re.sub(r"Очень приятно,\s*Сейчас[!]?","Очень приятно!", reply)
        reply = re.sub(r"\s{2,}", " ", reply).strip()

        return reply.strip()

    except Exception as e:
        print(f"Ошибка при запросе к Ollama: {e}")
        return "Извини, я не могу сейчас ответить 😔"


# === Основная логика общения ===
async def chat_with_selected_girl(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text.strip()

    # Проверяем дневной лимит
    if not can_send_today(user_id):
        import random
        await send_human_like_message(
            message.bot,
            message.chat.id,
            random.choice(limit_reached_phrases)
        )
        return

    # Увеличиваем счётчик
    increment_message_count(user_id)

    if user_id not in user_states:
        await message.answer("Выбери девушку, прежде чем начать общение ❤️")
        return

    # сначала проверяем явную подачу имени (только явные формы)
    if not get_user_name(user_id):
        name = extract_user_name(user_text)
        if name:
            set_user_name(user_id, name)
            await send_human_like_message(message.bot, message.chat.id, f"Очень приятно, {name}! 💖")
            return

    if check_message(user_text) or filter_prohibited(user_text):
        reply = (
            "Мне кажется, это не очень уместно 😅. "
            "Давай лучше поговорим о чём-то приятном?"
        )
        await send_human_like_message(message.bot, message.chat.id, reply)
        return

    girl_data = user_states[user_id]
    girl_name = girl_data.get('name', 'Девушка')
    persona = girl_data.get('persona_prompt', '')
    bio = girl_data.get('bio', '')
    girl_location = girl_data.get('location', '')
    timezone = girl_data.get('timezone', 'Europe/Moscow')  # default

    # если пользователь коротко ответил именем — обработка уже в extract_user_name, поэтому убираем угадку по  <=3 словам

    user_name = get_user_name(user_id)

    add_message(user_id, "user", user_text)
    history = get_dialog(user_id)
    history_text = ""
    for msg in history:
        if msg["role"] == "user":
            history_text += f"{user_name or 'Пользователь'}: {msg['content']}\n"
        else:
            history_text += f"{girl_name}: {msg['content']}\n"

    # получаем локальное время персонажа и готовим инструкцию для модели (англ.)
    local_time, period = get_local_time_str(timezone)
    time_instruction = (
        f"Current local time for the character: {local_time} (timezone: {timezone}). "
        f"When the user asks about the time, reply exactly with the time in format HH:MM and nothing else. "
        "Do not invent events, do not invent durations like 'hours two-two', and do not re-greet if you already greeted."
    )

    name_line = f"You already know the user's name: {user_name}." if user_name else ""
    # system_prompt — English (persona in YAML is English)
    system_prompt = (
        f"{persona}\n"
        f"Bio: {bio}\n"
        f"Location (as user-visible): {girl_location}\n\n"
        f"{time_instruction}\n\n"
        f"{name_line}\n\n"
        f"Conversation history:\n{history_text}"
    )

    reply = get_ai_response(user_text, system_prompt=system_prompt)
    await send_human_like_message(message.bot, message.chat.id, reply)
    add_message(user_id, "assistant", reply)


# === Выбор девушки ===
async def choose_girl_callback(query: types.CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "Выберите девушку для общения:",
        reply_markup=get_girl_selection_keyboard()
    )


async def chat_with_girl(query: types.CallbackQuery):
    await query.answer()

    girl_name_key = query.data.replace('chat_with_', '').strip().lower()
    girl_data = load_girl_data(girl_name_key)

    if not girl_data:
        await query.message.edit_text(f"Извини, данные для девушки {girl_name_key} не найдены.")
        return

    user_id = query.from_user.id
    user_states[user_id] = girl_data
    clear_dialog(user_id)

    await query.message.delete()

    photos = girl_data.get('assets', {}).get('photos', [])
    girl_name = girl_data.get('name', girl_name_key)
    first_message = girl_data.get('first_message', f"Привет! 😊 Я {girl_name}. А тебя как зовут?")
    greeting_text = get_greeting(girl_name_key)


    girl_location = girl_data.get('location', '')
    timezone = girl_data.get('timezone', 'Europe/Moscow')
    local_time, period = get_local_time_str(timezone)

    full_greeting = f"✨ {greeting_text}\n\n{first_message}"


    if photos:
        await query.message.answer_photo(
            photo=open(photos[0], 'rb'),
            caption=full_greeting
        )
    else:
        await send_human_like_message(query.bot, query.from_user.id, full_greeting, instant_first=True)

def can_send_today(user_id):
    """Проверяет, может ли пользователь ещё отправлять сообщения сегодня."""
    today = datetime.now().date()
    stats = _user_daily_stats.get(user_id)

    if not stats:
        _user_daily_stats[user_id] = {"count": 0, "date": today}
        return True

    # Сброс счётчика на следующий день
    if stats["date"] != today:
        _user_daily_stats[user_id] = {"count": 0, "date": today}
        return True

    if stats["count"] >= DAILY_MESSAGE_LIMIT:
        return False

    return True


def increment_message_count(user_id):
    """Увеличивает счётчик сообщений."""
    today = datetime.now().date()
    stats = _user_daily_stats.get(user_id, {"count": 0, "date": today})
    if stats["date"] != today:
        stats = {"count": 0, "date": today}
    stats["count"] += 1
    _user_daily_stats[user_id] = stats


def register(dp: Dispatcher):
    dp.register_callback_query_handler(choose_girl_callback, lambda c: c.data == "choose_girl")
    dp.register_callback_query_handler(chat_with_girl, lambda c: c.data.startswith("chat_with_"))
    dp.register_message_handler(chat_with_selected_girl, content_types=['text'])
