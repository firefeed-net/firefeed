from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple


class IDatabaseService(ABC):
    @abstractmethod
    async def mark_translation_as_published(self, translation_id: int, channel_id: int, message_id: int = None) -> bool:
        """Marks translation as published in Telegram channel."""
        pass

    @abstractmethod
    async def mark_original_as_published(self, news_id: str, channel_id: int, message_id: int = None) -> bool:
        """Marks original news as published in Telegram channel."""
        pass

    @abstractmethod
    async def get_translation_id(self, news_id: str, language: str) -> Optional[int]:
        """Gets translation ID from news_translations table."""
        pass

    @abstractmethod
    async def get_feed_cooldown_and_max_news(self, feed_id: int) -> Tuple[int, int]:
        """Gets cooldown minutes and max news per hour for feed."""
        pass

    @abstractmethod
    async def get_last_telegram_publication_time(self, feed_id: int) -> Optional[datetime]:
        """Get last Telegram publication time for feed."""
        pass

    @abstractmethod
    async def get_recent_telegram_publications_count(self, feed_id: int, minutes: int) -> int:
        """Get count of recent Telegram publications for feed."""
        pass