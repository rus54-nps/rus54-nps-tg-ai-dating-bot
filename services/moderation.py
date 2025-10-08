def check_message(message: str) -> bool:
    # Пример базовой функции фильтрации сообщений
    inappropriate_keywords = ["сексуальный", "неприличный", "порнография"]
    
    # Проверяем, содержит ли сообщение неподобающие слова
    for keyword in inappropriate_keywords:
        if keyword in message.lower():
            return True  # Сообщение не проходит модерацию

    return False  # Сообщение безопасно
