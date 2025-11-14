import logging
from typing import Dict, List

from ..interfaces.user_manager_interface import IUserManagerService
from ..models.user_state import UserStateManager

logger = logging.getLogger(__name__)


class UserManagerService(IUserManagerService):
    """Service for user management operations."""

    def __init__(self, user_manager, user_state_manager: UserStateManager):
        self.user_manager = user_manager
        self.user_state_manager = user_state_manager

    async def set_user_language(self, user_id: int, lang: str):
        """Sets user language in DB."""
        try:
            await self.user_manager.set_user_language(user_id, lang)
            self.user_state_manager.set_user_language(user_id, lang)
        except Exception as e:
            logger.error(f"Error setting language for {user_id}: {e}")

    async def get_user_language(self, user_id: int) -> str:
        """Gets user language from DB."""
        try:
            lang = await self.user_manager.get_user_language(user_id)
            if lang:
                self.user_state_manager.set_user_language(user_id, lang)
            return lang or "en"
        except Exception as e:
            logger.error(f"Error getting language for {user_id}: {e}")
            return "en"

    async def get_user_settings(self, user_id: int) -> Dict:
        """Gets user settings."""
        try:
            logger.info(f"Loading settings for user {user_id}")
            settings = await self.user_manager.get_user_settings(user_id)
            logger.info(f"Loaded settings for user {user_id}: {settings}")
            return settings
        except Exception as e:
            logger.error(f"Error getting settings for {user_id}: {e}")
            return {"subscriptions": [], "language": "en"}

    async def save_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Saves user settings."""
        try:
            logger.info(f"Saving settings for user {user_id}: subscriptions={subscriptions}, language={language}")
            result = await self.user_manager.save_user_settings(user_id, subscriptions, language)
            logger.info(f"Save result for user {user_id}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error saving settings for {user_id}: {e}")
            return False

    async def get_subscribers_for_category(self, category: str) -> List[Dict]:
        """Gets subscribers for category."""
        try:
            subscribers = await self.user_manager.get_subscribers_for_category(category)
            return subscribers
        except Exception as e:
            logger.error(f"Error getting subscribers for category {category}: {e}")
            return []

    async def confirm_telegram_link(self, user_id: int, link_code: str) -> bool:
        """Confirms Telegram link."""
        try:
            success = await self.user_manager.confirm_telegram_link(user_id, link_code)
            return success
        except Exception as e:
            logger.error(f"Error confirming Telegram link for {user_id}: {e}")
            return False