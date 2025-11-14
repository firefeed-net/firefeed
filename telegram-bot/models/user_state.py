from typing import Dict, Any, Optional
import time


class UserStateManager:
    """Manages user states, menus, and languages with TTL."""

    def __init__(self, ttl_seconds: int = 24 * 60 * 60):
        self.ttl_seconds = ttl_seconds
        self.user_states: Dict[int, Dict[str, Any]] = {}  # {user_id: {"current_subs": [...], "language": "en", "last_access": timestamp}}
        self.user_current_menus: Dict[int, Dict[str, Any]] = {}  # {user_id: "main", "last_access": timestamp}
        self.user_languages: Dict[int, Dict[str, Any]] = {}  # {user_id: "en", "last_access": timestamp}

    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Gets user state if not expired."""
        if user_id in self.user_states:
            data = self.user_states[user_id]
            if isinstance(data, dict) and data.get("last_access", 0) > time.time() - self.ttl_seconds:
                data["last_access"] = time.time()
                return data
            else:
                del self.user_states[user_id]
        return None

    def set_user_state(self, user_id: int, state: Dict[str, Any]):
        """Sets user state."""
        state["last_access"] = time.time()
        self.user_states[user_id] = state

    def get_user_current_menu(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Gets user current menu if not expired."""
        if user_id in self.user_current_menus:
            data = self.user_current_menus[user_id]
            if isinstance(data, dict) and data.get("last_access", 0) > time.time() - self.ttl_seconds:
                data["last_access"] = time.time()
                return data
            else:
                del self.user_current_menus[user_id]
        return None

    def set_user_current_menu(self, user_id: int, menu: Dict[str, Any]):
        """Sets user current menu."""
        menu["last_access"] = time.time()
        self.user_current_menus[user_id] = menu

    def get_user_language(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Gets user language if not expired."""
        if user_id in self.user_languages:
            data = self.user_languages[user_id]
            if isinstance(data, dict) and data.get("last_access", 0) > time.time() - self.ttl_seconds:
                data["last_access"] = time.time()
                return data
            else:
                del self.user_languages[user_id]
        return None

    def set_user_language(self, user_id: int, language: str):
        """Sets user language."""
        self.user_languages[user_id] = {"language": language, "last_access": time.time()}

    def cleanup_expired_data(self):
        """Clears expired user data."""
        current_time = time.time()
        expired_threshold = current_time - self.ttl_seconds

        # Clear USER_STATES
        expired_states = [uid for uid, data in self.user_states.items()
                          if isinstance(data, dict) and data.get("last_access", 0) < expired_threshold]
        for uid in expired_states:
            del self.user_states[uid]

        # Clear USER_CURRENT_MENUS
        expired_menus = [uid for uid, data in self.user_current_menus.items()
                         if isinstance(data, dict) and data.get("last_access", 0) < expired_threshold]
        for uid in expired_menus:
            del self.user_current_menus[uid]

        # Clear USER_LANGUAGES
        expired_langs = [uid for uid, data in self.user_languages.items()
                         if isinstance(data, dict) and data.get("last_access", 0) < expired_threshold]
        for uid in expired_langs:
            del self.user_languages[uid]

        return len(expired_states), len(expired_menus), len(expired_langs)