import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


def chat_with_ollama(message: str, personality_prompt: str = "") -> str:
    """
    Отправляет сообщение в Ollama и возвращает ответ модели
    """
    url = f"{OLLAMA_API}/api/chat"
    data = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": personality_prompt},
            {"role": "user", "content": message}
        ]
    }

    try:
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()

        full_reply = ""
        for line in response.iter_lines():
            if line:
                chunk = line.decode("utf-8")
                if "\"content\"" in chunk:
                    text_part = chunk.split("\"content\":\"")[-1].split("\"")[0]
                    full_reply += text_part
        return full_reply.strip() or "⚠️ Пустой ответ от модели."
    except Exception as e:
        return f"Ошибка при запросе к Ollama: {e}"
