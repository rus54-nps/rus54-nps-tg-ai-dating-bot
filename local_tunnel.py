import subprocess
import re
import time
import requests

LOCAL_PORT = 11434

def check_ollama_alive():
    try:
        r = requests.get(f"http://127.0.0.1:{LOCAL_PORT}/api/tags", timeout=2)
        if r.status_code == 200:
            print("✅ Ollama запущена локально.")
            return True
    except Exception:
        pass
    print("❌ Ollama не отвечает на localhost:11434 — запусти `ollama serve`!")
    return False


def create_tunnel():
    print("🚀 Создаю туннель через serveo.net...")

    # ✅ Важно: пробрасываем именно 11434:11434
    command = [
        "ssh", "-o", "StrictHostKeyChecking=no", "-R",
        f"11434:127.0.0.1:{LOCAL_PORT}", "serveo.net"
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    url = None
    start_time = time.time()

    for line in iter(process.stdout.readline, ''):
        if "Forwarding TCP connections from" in line:
            match = re.search(r"serveo\.net:\d+", line)
            if match:
                url = f"{match.group(0)}"
                break
        if time.time() - start_time > 25:
            break

    if url:
        print(f"✅ Туннель создан: {url}")
        print("🌐 Используй это в Railway в переменной OLLAMA_API как:")
        print(f"👉 http://{url}")
        return f"http://{url}", process
    else:
        print("❌ Не удалось получить URL. Возможно, SSH или Serveo заблокирован провайдером.")
        process.terminate()
        return None, None


if __name__ == "__main__":
    if not check_ollama_alive():
        exit(1)

    url, proc = create_tunnel()
    if url:
        print("🔁 Проверяю доступ через туннель...")
        try:
            test = requests.get(f"{url}/api/tags", timeout=10)
            if test.status_code == 200:
                print("✅ Тест успешен — туннель работает, Ollama доступна онлайн!")
            else:
                print(f"⚠️ Сервер ответил, но не корректно: {test.status_code}")
        except Exception as e:
            print(f"❌ Ошибка при проверке туннеля: {e}")

        print("🟢 Туннель активен. Не закрывай это окно, пока бот работает.")
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n⛔ Завершаю туннель...")
            proc.terminate()
