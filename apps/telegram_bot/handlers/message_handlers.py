# telegram_bot/handlers/message_handlers.py - Message handlers
import logging

from telegram import Update
from telegram.ext import ContextTypes

from apps.telegram_bot.services.user_state_service import get_current_user_language, set_current_user_language, set_user_menu
from apps.telegram_bot.utils.keyboard_utils import get_main_menu_keyboard
from apps.telegram_bot.translations import get_message

logger = logging.getLogger(__name__)


async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for menu selection."""
    user_id = update.effective_user.id
    lang = await get_current_user_language(user_id)
    text = update.message.text
    menu_actions = {
        get_message("menu_settings", lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['settings_command']).settings_command(u, c),
        get_message("menu_help", lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['help_command']).help_command(u, c),
        get_message("menu_status", lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['status_command']).status_command(u, c),
        get_message("menu_language", lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['change_language_command']).change_language_command(u, c),
    }
    action = menu_actions.get(text)
    if action:
        await action(update, context)
        return
    all_languages = ["en", "ru", "de", "fr"]
    for check_lang in all_languages:
        if text in [get_message(f"menu_{m}", check_lang) for m in ["settings", "help", "status", "language"]]:
            await set_current_user_language(user_id, check_lang)
            new_menu_actions = {
                get_message("menu_settings", check_lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['settings_command']).settings_command(u, c),
                get_message("menu_help", check_lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['help_command']).help_command(u, c),
                get_message("menu_status", check_lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['status_command']).status_command(u, c),
                get_message("menu_language", check_lang): lambda u, c: __import__('apps.telegram_bot.handlers.command_handlers', fromlist=['change_language_command']).change_language_command(u, c),
            }
            new_action = new_menu_actions.get(text)
            if new_action:
                await new_action(update, context)
            return
    logger.info(f"Unknown menu selection for {user_id}: {text}")


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for debug messages."""
    user_id = update.effective_user.id
    lang = await get_current_user_language(user_id)
    await update.message.reply_text(get_message("bot_active", lang), reply_markup=get_main_menu_keyboard(lang))
    set_user_menu(user_id, "main")