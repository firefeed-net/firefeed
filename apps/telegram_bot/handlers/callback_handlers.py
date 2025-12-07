# telegram_bot/handlers/callback_handlers.py - Callback query handlers
import logging

from telegram import Update
from telegram.ext import ContextTypes

from apps.telegram_bot.services import user_state_service
from apps.telegram_bot.services.user_state_service import (
    get_current_user_language, set_current_user_language, get_user_state,
    update_user_state, clear_user_state
)
from apps.telegram_bot.services.api_service import get_categories
from apps.telegram_bot.utils.keyboard_utils import get_main_menu_keyboard, get_settings_keyboard
from apps.telegram_bot.translations import get_message, LANG_NAMES

logger = logging.getLogger(__name__)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for callback buttons."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        if user_state_service.telegram_user_service is None:
            logger.warning(f"telegram_user_service not initialized for button handler for {user_id}")
            await context.bot.send_message(
                chat_id=user_id,
                text=get_message("settings_error", await get_current_user_language(user_id)),
                reply_markup=get_main_menu_keyboard(await get_current_user_language(user_id)),
            )
            from apps.telegram_bot.services.user_state_service import set_user_menu
            set_user_menu(user_id, "main")
            return
        if not get_user_state(user_id):
            if user_state_service.telegram_user_service is not None:
                subs = await user_state_service.telegram_user_service.get_user_subscriptions(user_id)
                current_subs = subs if isinstance(subs, list) else []
            else:
                current_subs = []
                logger.error(f"telegram_user_service not initialized for button handler for {user_id}")
            update_user_state(user_id, {"current_subs": current_subs, "language": await get_current_user_language(user_id)})
        state = get_user_state(user_id)
        current_lang = state["language"] if state else await get_current_user_language(user_id)
        if query.data.startswith("toggle_"):
            category = query.data.split("_", 1)[1]
            current_subs = state["current_subs"] if state else []
            if category in current_subs:
                current_subs.remove(category)
            else:
                current_subs.append(category)
            if state:
                state["current_subs"] = current_subs
            try:
                await query.message.delete()
            except Exception:
                pass
            await _show_settings_menu_from_callback(context.bot, query.message.chat_id, user_id)
        elif query.data == "save_settings":
            # Save category names as strings
            logger.info(
                f"Saving settings for user {user_id}: subscriptions={state['current_subs'] if state else []}, language={current_lang}"
            )
            if user_state_service.telegram_user_service is not None:
                result = await user_state_service.telegram_user_service.save_user_settings(user_id, state["current_subs"] if state else [], current_lang)
                logger.info(f"Save result for user {user_id}: {result}")
                clear_user_state(user_id)
            else:
                logger.error(f"telegram_user_service not initialized for save_settings for {user_id}")
                # Do not clear state, keep it for retry
            try:
                await query.message.delete()
            except Exception:
                pass
            # Show current subscriptions after saving settings
            if user_state_service.telegram_user_service is not None:
                settings = await user_state_service.telegram_user_service.get_user_settings(user_id)
                categories = settings["subscriptions"]
                categories_text = ", ".join(categories) if categories else get_message("no_subscriptions", current_lang)
                status_text = get_message(
                    "settings_saved_with_subs", current_lang, categories=categories_text
                )
            else:
                status_text = get_message("settings_saved", current_lang)
            await context.bot.send_message(
                chat_id=user_id, text=status_text, reply_markup=get_main_menu_keyboard(current_lang)
            )
            from apps.telegram_bot.services.user_state_service import set_user_menu
            set_user_menu(user_id, "main")
        elif query.data.startswith("lang_"):
            lang = query.data.split("_", 1)[1]
            await set_current_user_language(user_id, lang)
            if state:
                state["language"] = lang
            try:
                await query.message.delete()
            except Exception:
                pass
            user = await context.bot.get_chat(user_id)
            welcome_text = (
                get_message("language_changed", lang, language=LANG_NAMES.get(lang, "English"))
                + "\n"
                + get_message("welcome", lang, user_name=user.first_name)
            )
            await context.bot.send_message(
                chat_id=user_id, text=welcome_text, reply_markup=get_main_menu_keyboard(lang)
            )
            from apps.telegram_bot.services.user_state_service import set_user_menu
            set_user_menu(user_id, "main")
        elif query.data == "change_lang":
            current_lang = await get_current_user_language(user_id)
            keyboard = get_language_selection_keyboard()
            await query.message.edit_text(
                text=get_message("language_select", current_lang), reply_markup=keyboard
            )
            from apps.telegram_bot.services.user_state_service import set_user_menu
            set_user_menu(user_id, "language")
    except Exception as e:
        logger.error(f"Error processing button for {user_id}: {e}")
        current_lang = await get_current_user_language(user_id)
        await context.bot.send_message(
            chat_id=user_id,
            text=get_message("button_error", current_lang),
            reply_markup=get_main_menu_keyboard(current_lang),
        )
        from apps.telegram_bot.services.user_state_service import set_user_menu
        set_user_menu(user_id, "main")


async def _show_settings_menu_from_callback(bot, chat_id: int, user_id: int):
    """Displays settings menu from callback."""
    await _show_settings_menu(bot, chat_id, user_id)


async def _show_settings_menu(bot, chat_id: int, user_id: int):
    """Displays settings menu."""
    state = get_user_state(user_id)
    if not state:
        return
    current_subs = state["current_subs"]
    current_lang = state["language"]
    try:
        categories = await get_categories()
        keyboard = get_settings_keyboard(categories, current_subs, current_lang)
        await bot.send_message(
            chat_id=chat_id, text=get_message("settings_title", current_lang), reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in _show_settings_menu for {user_id}: {e}")