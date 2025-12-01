# telegram_bot/utils/keyboard_utils.py - Keyboard creation utilities
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from telegram_bot.translations import get_message


def get_main_menu_keyboard(lang="en"):
    """Creates main menu keyboard."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(get_message("menu_settings", lang)), KeyboardButton(get_message("menu_help", lang))],
            [KeyboardButton(get_message("menu_status", lang)), KeyboardButton(get_message("menu_language", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=get_message("menu_placeholder", lang),
    )


def get_language_selection_keyboard():
    """Creates language selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(categories, current_subs, current_lang):
    """Creates settings keyboard with category toggles."""
    keyboard = []
    for category in categories:
        category_name = category.get("name", str(category))
        is_selected = category_name in current_subs
        text = f"{'✅ ' if is_selected else '🔲 '}{category_name.capitalize()}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"toggle_{category_name}")])
    keyboard.append([InlineKeyboardButton(get_message("save_button", current_lang), callback_data="save_settings")])
    return InlineKeyboardMarkup(keyboard)