# telegram_bot/services/user_state_service.py - User state management service
import time
from typing import Dict, Any, Optional

from apps.telegram_bot.utils.cleanup_utils import cleanup_expired_user_data
from di_container import get_service
from interfaces import ITelegramUserService

# Global user state storage
USER_STATES: Dict[int, Dict[str, Any]] = {}
USER_CURRENT_MENUS: Dict[int, Dict[str, Any]] = {}
USER_LANGUAGES: Dict[int, str] = {}

# Global telegram user service instance
telegram_user_service = None


async def initialize_user_manager(context=None):
    """Initialize telegram user service instance."""
    global telegram_user_service
    if telegram_user_service is None:
        try:
            telegram_user_service = get_service(ITelegramUserService)
            # Import here to avoid circular imports
            import logging
            logger = logging.getLogger(__name__)
            logger.info("telegram_user_service initialized successfully")
        except Exception as e:
            # Import here to avoid circular imports
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize telegram_user_service: {e}")
            raise


async def set_current_user_language(user_id: int, lang: str):
    """Sets user language in DB and memory."""
    global telegram_user_service
    try:
        await telegram_user_service.set_user_language(user_id, lang)
        USER_LANGUAGES[user_id] = {"language": lang, "last_access": time.time()}
    except Exception as e:
        # Log error but don't raise - language setting is not critical
        pass


async def get_current_user_language(user_id: int) -> str:
    """Gets current user language from memory or DB."""
    if user_id in USER_LANGUAGES:
        data = USER_LANGUAGES[user_id]
        if isinstance(data, dict):
            data["last_access"] = time.time()
            return data["language"]
        else:
            # Update old format
            USER_LANGUAGES[user_id] = {"language": data, "last_access": time.time()}
            return data

    try:
        global telegram_user_service
        lang = await telegram_user_service.get_user_language(user_id)
        if lang:
            USER_LANGUAGES[user_id] = {"language": lang, "last_access": time.time()}
        return lang or "en"
    except Exception as e:
        return "en"


def update_user_state(user_id: int, state_data: Dict[str, Any]):
    """Update user state in memory."""
    state_data["last_access"] = time.time()
    USER_STATES[user_id] = state_data


def get_user_state(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user state from memory."""
    state = USER_STATES.get(user_id)
    if state:
        state["last_access"] = time.time()
    return state


def set_user_menu(user_id: int, menu: str):
    """Set current user menu."""
    USER_CURRENT_MENUS[user_id] = {"menu": menu, "last_access": time.time()}


def get_user_menu(user_id: int) -> Optional[str]:
    """Get current user menu."""
    menu_data = USER_CURRENT_MENUS.get(user_id)
    if menu_data:
        menu_data["last_access"] = time.time()
        return menu_data.get("menu")
    return None


async def cleanup_expired_data(context=None):
    """Clean up expired user data."""
    states_cleared, menus_cleared, langs_cleared = cleanup_expired_user_data(
        USER_STATES, USER_CURRENT_MENUS, USER_LANGUAGES
    )
    if states_cleared or menus_cleared or langs_cleared:
        # Import here to avoid circular imports
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[CLEANUP] Cleared expired data: states={states_cleared}, menus={menus_cleared}, langs={langs_cleared}")


def clear_user_state(user_id: int):
    """Clear user state."""
    USER_STATES.pop(user_id, None)
    USER_CURRENT_MENUS.pop(user_id, None)