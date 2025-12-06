# interfaces/user_interfaces.py - User management interfaces
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class IUserRepository(ABC):
    """Interface for user repository operations"""

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def create_user(self, email: str, password_hash: str, language: str) -> Optional[Dict[str, Any]]:
        """Create new user"""
        pass

    @abstractmethod
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        pass

    @abstractmethod
    async def save_verification_code(self, user_id: int, code: str, expires_at: datetime) -> bool:
        """Save email verification code"""
        pass

    @abstractmethod
    async def activate_user_and_use_verification_code(self, user_id: int, code: str) -> bool:
        """Activate user with verification code"""
        pass

    @abstractmethod
    async def save_password_reset_token(self, user_id: int, token: str, expires_at: datetime) -> bool:
        """Save password reset token"""
        pass

    @abstractmethod
    async def confirm_password_reset_transaction(self, token: str, new_password_hash: str) -> bool:
        """Confirm password reset"""
        pass

    @abstractmethod
    async def delete_password_reset_token(self, token: str) -> bool:
        """Delete password reset token"""
        pass

    # Telegram user methods
    @abstractmethod
    async def get_telegram_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get Telegram user settings"""
        pass

    @abstractmethod
    async def save_telegram_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save Telegram user settings"""
        pass

    @abstractmethod
    async def set_telegram_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set Telegram user language"""
        pass

    @abstractmethod
    async def get_telegram_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get Telegram subscribers for category"""
        pass

    @abstractmethod
    async def remove_telegram_blocked_user(self, user_id: int) -> bool:
        """Remove blocked Telegram user"""
        pass

    @abstractmethod
    async def get_all_telegram_users(self) -> List[int]:
        """Get all Telegram users"""
        pass

    # Web user Telegram linking methods
    @abstractmethod
    async def generate_telegram_link_code(self, user_id: int) -> str:
        """Generate Telegram link code"""
        pass

    @abstractmethod
    async def confirm_telegram_link(self, telegram_id: int, link_code: str) -> bool:
        """Confirm Telegram link"""
        pass

    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        pass

    @abstractmethod
    async def unlink_telegram(self, user_id: int) -> bool:
        """Unlink Telegram account"""
        pass


class ITelegramUserService(ABC):
    """Interface for Telegram bot user management"""

    @abstractmethod
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        pass

    @abstractmethod
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update user settings"""
        pass

    @abstractmethod
    async def get_user_language(self, user_id: int) -> Optional[str]:
        """Get user language"""
        pass

    @abstractmethod
    async def set_user_language(self, user_id: int, language: str) -> bool:
        """Set user language"""
        pass

    @abstractmethod
    async def get_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for category"""
        pass

    @abstractmethod
    async def confirm_telegram_link(self, user_id: int, link_code: str) -> bool:
        """Confirm Telegram account linking"""
        pass


class IWebUserService(ABC):
    """Interface for web user management and Telegram linking"""

    @abstractmethod
    async def generate_telegram_link_code(self, user_id: int) -> str:
        """Generate link code for Telegram"""
        pass

    @abstractmethod
    async def confirm_telegram_link(self, telegram_id: int, link_code: str) -> bool:
        """Confirm Telegram link"""
        pass

    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get web user by Telegram ID"""
        pass

    @abstractmethod
    async def unlink_telegram(self, user_id: int) -> bool:
        """Unlink Telegram account"""
        pass


class IUserManager(ABC):
    """Interface for unified user management (backward compatibility)"""

    @abstractmethod
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        pass

    @abstractmethod
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update user settings"""
        pass

    @abstractmethod
    async def get_user_language(self, user_id: int) -> Optional[str]:
        """Get user language"""
        pass

    @abstractmethod
    async def set_user_language(self, user_id: int, language: str) -> bool:
        """Set user language"""
        pass

    @abstractmethod
    async def get_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for category"""
        pass

    @abstractmethod
    async def confirm_telegram_link(self, user_id: int, link_code: str) -> bool:
        """Confirm Telegram account linking"""
        pass

    @abstractmethod
    async def generate_telegram_link_code(self, user_id: int) -> str:
        """Generate link code for Telegram"""
        pass