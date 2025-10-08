import aiohttp
import os

OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

async def get_ai_response(messages: list) -> str:
    """
    messages = [{"role": "system", "content": ...}, {"role": "user", "content": ...}, ...]
    """
    url = f"{OLLAMA_API}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=120) as resp:
                data = await resp.json()
                return data.get("message", {}).get("content", "❌ Ошибка при получении ответа.")
    except Exception as e:
        return f"⚠️ Ошибка соединения с AI: {e}"
