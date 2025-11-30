# user_manager.py - Backward compatibility wrapper
import logging
from typing import Optional, Dict, Any
from services.user.telegram_user_service import TelegramUserService
from services.user.web_user_service import WebUserService
from interfaces import IUserManager

logger = logging.getLogger(__name__)


class UserManager(IUserManager):
    """Backward compatibility wrapper for UserManager - delegates to specialized services"""

    def __init__(self):
        self.telegram_service = TelegramUserService()
        self.web_service = WebUserService()

    # --- Telegram user methods (delegated to TelegramUserService) ---

    async def get_user_settings(self, user_id):
        """Get user settings (Telegram bot)"""
        return await self.telegram_service.get_user_settings(user_id)

    async def save_user_settings(self, user_id, subscriptions, language):
        """Save user settings (Telegram bot)"""
        return await self.telegram_service.save_user_settings(user_id, subscriptions, language)

    async def set_user_language(self, user_id, lang_code):
        """Set user language (Telegram bot)"""
        return await self.telegram_service.set_user_language(user_id, lang_code)

    async def get_user_subscriptions(self, user_id):
        """Get user subscriptions (Telegram bot)"""
        return await self.telegram_service.get_user_subscriptions(user_id)

    async def get_user_language(self, user_id):
        """Get user language (Telegram bot)"""
        return await self.telegram_service.get_user_language(user_id)

    async def get_subscribers_for_category(self, category):
        """Get subscribers for category (Telegram bot)"""
        return await self.telegram_service.get_subscribers_for_category(category)

    async def get_all_users(self):
        """Get all users (Telegram bot)"""
        return await self.telegram_service.get_all_users()

    async def remove_blocked_user(self, user_id: int) -> bool:
        """Remove blocked user (Telegram bot)"""
        return await self.telegram_service.remove_blocked_user(user_id)

    # --- Web user methods (delegated to WebUserService) ---

    async def generate_telegram_link_code(self, user_id: int) -> str:
        """Generate Telegram link code (Web users)"""
        return await self.web_service.generate_telegram_link_code(user_id)

    async def confirm_telegram_link(self, telegram_id: int, link_code: str) -> bool:
        """Confirm Telegram link (Web users)"""
        return await self.web_service.confirm_telegram_link(telegram_id, link_code)

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get web user by Telegram ID"""
        return await self.web_service.get_user_by_telegram_id(telegram_id)

    async def unlink_telegram(self, user_id: int) -> bool:
        """Unlink Telegram account (Web users)"""
        return await self.web_service.unlink_telegram(user_id)
