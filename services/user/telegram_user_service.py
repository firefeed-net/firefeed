# services/user/telegram_user_service.py
import logging
from typing import List, Dict, Any
from interfaces import ITelegramUserService, IUserRepository

logger = logging.getLogger(__name__)


class TelegramUserService(ITelegramUserService):
    """Service for managing Telegram bot users and their preferences"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        return await self.user_repository.get_telegram_user_settings(user_id)

    async def save_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save user settings"""
        return await self.user_repository.save_telegram_user_settings(user_id, subscriptions, language)

    async def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set user language"""
        return await self.user_repository.set_telegram_user_language(user_id, lang_code)

    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Get user subscriptions only"""
        settings = await self.get_user_settings(user_id)
        return settings["subscriptions"]

    async def get_user_language(self, user_id: int) -> str:
        """Get user language only"""
        settings = await self.get_user_settings(user_id)
        return settings["language"]

    async def get_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for category"""
        return await self.user_repository.get_telegram_subscribers_for_category(category)

    async def get_all_users(self) -> List[int]:
        """Get all users"""
        return await self.user_repository.get_all_telegram_users()

    async def remove_blocked_user(self, user_id: int) -> bool:
        """Remove blocked user"""
        return await self.user_repository.remove_telegram_blocked_user(user_id)