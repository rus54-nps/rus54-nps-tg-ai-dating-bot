from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("Выбрать девушку", callback_data="choose_girl"))
    return keyboard

def get_girl_selection_keyboard():
    # Кнопки для выбора двух бесплатных девушек
    girls = ["София", "Вика"]
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for girl in girls:
        keyboard.add(InlineKeyboardButton(girl, callback_data=f"chat_with_{girl.lower()}"))
    return keyboard
