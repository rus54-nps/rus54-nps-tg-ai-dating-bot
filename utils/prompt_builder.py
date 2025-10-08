def build_prompt(user_message: str, girl_name: str) -> str:
    return f"Пользователь пишет девушке {girl_name}: {user_message}\nОтветь естественно, от лица {girl_name}."
