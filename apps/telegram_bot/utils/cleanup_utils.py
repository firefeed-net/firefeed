# telegram_bot/utils/cleanup_utils.py - Data cleanup utilities
import time
from typing import Dict, Any

# Configuration moved to DI
from di_container import get_service

USER_DATA_TTL_SECONDS = None

def get_user_data_ttl():
    global USER_DATA_TTL_SECONDS
    if USER_DATA_TTL_SECONDS is None:
        config_obj = get_service(dict)
        USER_DATA_TTL_SECONDS = config_obj.get('USER_DATA_TTL_SECONDS', 86400)
    return USER_DATA_TTL_SECONDS


def cleanup_expired_user_data(user_states: Dict[int, Any], user_current_menus: Dict[int, Any], user_languages: Dict[int, Any]):
    """Clears expired user data (older than 24 hours)."""
    current_time = time.time()
    expired_threshold = current_time - get_user_data_ttl()

    # Clear USER_STATES
    expired_states = [uid for uid, data in user_states.items()
                      if isinstance(data, dict) and data.get("last_access", 0) < expired_threshold]
    for uid in expired_states:
        del user_states[uid]

    # Clear USER_CURRENT_MENUS
    expired_menus = [uid for uid, data in user_current_menus.items()
                     if isinstance(data, dict) and data.get("last_access", 0) < expired_threshold]
    for uid in expired_menus:
        del user_current_menus[uid]

    # Clear USER_LANGUAGES
    expired_langs = [uid for uid, data in user_languages.items()
                     if isinstance(data, dict) and data.get("last_access", 0) < expired_threshold]
    for uid in expired_langs:
        del user_languages[uid]

    return len(expired_states), len(expired_menus), len(expired_langs)