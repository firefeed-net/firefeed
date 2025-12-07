# services/user/web_user_service.py
import logging
from typing import Optional, Dict, Any
from interfaces import IWebUserService, IUserRepository

logger = logging.getLogger(__name__)


class WebUserService(IWebUserService):
    """Service for managing web users and Telegram linking"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def generate_telegram_link_code(self, user_id: int) -> str:
        """Generate code for linking Telegram account"""
        return await self.user_repository.generate_telegram_link_code(user_id)

    async def confirm_telegram_link(self, telegram_id: int, link_code: str) -> bool:
        """Confirm Telegram account linking by code"""
        return await self.user_repository.confirm_telegram_link(telegram_id, link_code)

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get web user by Telegram ID"""
        return await self.user_repository.get_user_by_telegram_id(telegram_id)

    async def unlink_telegram(self, user_id: int) -> bool:
        """Unlink Telegram account from web user"""
        return await self.user_repository.unlink_telegram(user_id)