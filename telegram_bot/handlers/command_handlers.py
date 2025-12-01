# telegram_bot/handlers/command_handlers.py - Command handlers
import logging

from telegram import Update
from telegram.ext import ContextTypes

import telegram_bot.services.user_state_service as user_state_service
from telegram_bot.services.user_state_service import (
    get_current_user_language, set_current_user_language, set_user_menu,
    update_user_state, get_user_state, clear_user_state
)
from telegram_bot.services.api_service import get_categories
from telegram_bot.utils.keyboard_utils import get_main_menu_keyboard, get_language_selection_keyboard
from telegram_bot.translations import get_message, LANG_NAMES

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user
    user_id = user.id
    lang = await get_current_user_language(user_id)
    welcome_text = get_message("welcome", lang, user_name=user.first_name)
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(lang))
    set_user_menu(user_id, "main")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /settings command."""
    user_id = update.effective_user.id
    try:
        lang = await get_current_user_language(user_id)
        logger.info(f"Loading settings for user {user_id}")
        if user_state_service.user_manager is not None:
            settings = await user_state_service.user_manager.get_user_settings(user_id)
            logger.info(f"Loaded settings for user {user_id}: {settings}")
            current_subs = settings["subscriptions"] if isinstance(settings["subscriptions"], list) else []
            update_user_state(user_id, {"current_subs": current_subs, "language": settings["language"]})
            await _show_settings_menu(context.bot, update.effective_chat.id, user_id)
            set_user_menu(user_id, "settings")
        else:
            logger.error(f"user_manager not initialized for /settings command for {user_id}")
            await update.message.reply_text(get_message("settings_error", lang))
    except Exception as e:
        logger.error(f"Error in /settings command for {user_id}: {e}")
        lang = await get_current_user_language(user_id)
        await update.message.reply_text(get_message("settings_error", lang))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    user_id = update.effective_user.id
    lang = await get_current_user_language(user_id)
    help_text = get_message("help_text", lang)
    await update.message.reply_text(help_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))
    set_user_menu(user_id, "main")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command."""
    user_id = update.effective_user.id
    lang = await get_current_user_language(user_id)
    if user_state_service.user_manager is not None:
        settings = await user_state_service.user_manager.get_user_settings(user_id)
        categories = settings["subscriptions"]
        categories_text = ", ".join(categories) if categories else get_message("no_subscriptions", lang)
        status_text = get_message(
            "status_text", lang, language=LANG_NAMES.get(settings['language'], 'English'), categories=categories_text
        )
        await update.message.reply_text(status_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))
        set_user_menu(user_id, "main")
    else:
        logger.error(f"user_manager not initialized for /status command for {user_id}")
        await update.message.reply_text(get_message("settings_error", lang), reply_markup=get_main_menu_keyboard(lang))
        set_user_menu(user_id, "main")


async def change_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for language change command."""
    user_id = update.effective_user.id
    lang = await get_current_user_language(user_id)
    keyboard = get_language_selection_keyboard()
    await update.message.reply_text(get_message("language_select", lang), reply_markup=keyboard)
    set_user_menu(user_id, "language")


async def link_telegram_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /link command to link Telegram account."""
    user_id = update.effective_user.id
    lang = await get_current_user_language(user_id)

    if not context.args:
        await update.message.reply_text(
            "Usage: /link <link_code>\n\n" "Get the link code in your personal account on the site.",
            reply_markup=get_main_menu_keyboard(lang),
        )
        set_user_menu(user_id, "main")
        return

    link_code = context.args[0].strip()

    # Check code via UserManager
    if user_state_service.user_manager is not None:
        success = await user_state_service.user_manager.confirm_telegram_link(user_id, link_code)
    else:
        success = False
        logger.error(f"user_manager not initialized for /link command for {user_id}")

    if success:
        await update.message.reply_text(
            "✅ Your Telegram account has been successfully linked to your site account!\n\n"
            "Now you can manage settings through the site or bot.",
            reply_markup=get_main_menu_keyboard(lang),
        )
    else:
        await update.message.reply_text(
            "❌ Link code is invalid or expired.\n\n"
            "Please generate a new code in your personal account on the site.",
            reply_markup=get_main_menu_keyboard(lang),
        )

    set_user_menu(user_id, "main")


async def _show_settings_menu(bot, chat_id: int, user_id: int):
    """Displays settings menu."""
    state = get_user_state(user_id)
    if not state:
        return
    current_subs = state["current_subs"]
    current_lang = state["language"]
    try:
        categories = await get_categories()
        keyboard = []
        for category in categories:
            category_name = category.get("name", str(category))
            is_selected = category_name in current_subs
            text = f"{'✅ ' if is_selected else '🔲 '}{category_name.capitalize()}"
            from telegram import InlineKeyboardButton
            keyboard.append([InlineKeyboardButton(text, callback_data=f"toggle_{category_name}")])
        keyboard.append([InlineKeyboardButton(get_message("save_button", current_lang), callback_data="save_settings")])
        from telegram import InlineKeyboardMarkup
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            chat_id=chat_id, text=get_message("settings_title", current_lang), reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in _show_settings_menu for {user_id}: {e}")