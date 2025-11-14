from abc import ABC, abstractmethod
from typing import Dict, List


class IUserManagerService(ABC):
    @abstractmethod
    async def set_user_language(self, user_id: int, lang: str):
        """Sets user language in DB."""
        pass

    @abstractmethod
    async def get_user_language(self, user_id: int) -> str:
        """Gets user language from DB."""
        pass

    @abstractmethod
    async def get_user_settings(self, user_id: int) -> Dict:
        """Gets user settings."""
        pass

    @abstractmethod
    async def save_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Saves user settings."""
        pass

    @abstractmethod
    async def get_subscribers_for_category(self, category: str) -> List[Dict]:
        """Gets subscribers for category."""
        pass

    @abstractmethod
    async def confirm_telegram_link(self, user_id: int, link_code: str) -> bool:
        """Confirms Telegram link."""
        pass