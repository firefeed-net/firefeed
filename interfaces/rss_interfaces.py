# interfaces/rss_interfaces.py - RSS processing interfaces
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class IRSSFetcher(ABC):
    """Interface for RSS feed fetching and parsing"""

    @abstractmethod
    async def fetch_feed(self, feed_info: Dict[str, Any], headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed"""
        pass

    @abstractmethod
    async def fetch_feeds(self, feeds_info: List[Dict[str, Any]], headers: Dict[str, str]) -> List[List[Dict[str, Any]]]:
        """Fetch and parse multiple RSS feeds concurrently"""
        pass


class IRSSValidator(ABC):
    """Interface for RSS feed validation"""

    @abstractmethod
    async def validate_feed(self, url: str, headers: Dict[str, str]) -> bool:
        """Validate if URL contains valid RSS feed"""
        pass


class IRSSStorage(ABC):
    """Interface for RSS data storage operations"""

    @abstractmethod
    async def save_rss_item(self, rss_item: Dict[str, Any], feed_id: int) -> Optional[str]:
        """Save RSS item to database"""
        pass

    @abstractmethod
    async def save_translations(self, news_id: str, translations: Dict[str, Dict[str, str]]) -> bool:
        """Save translations for RSS item"""
        pass

    @abstractmethod
    async def get_feed_cooldown(self, feed_id: int) -> int:
        """Get cooldown minutes for feed"""
        pass

    @abstractmethod
    async def get_feed_max_news_per_hour(self, feed_id: int) -> int:
        """Get max news per hour for feed"""
        pass

    @abstractmethod
    async def get_last_published_time(self, feed_id: int) -> Optional[datetime]:
        """Get last published time for feed"""
        pass

    @abstractmethod
    async def get_recent_items_count(self, feed_id: int, minutes: int) -> int:
        """Get count of recent items for feed"""
        pass

    @abstractmethod
    async def get_feeds_by_category(self, category_name: str) -> List[Dict[str, Any]]:
        """Get feeds by category name"""
        pass

    @abstractmethod
    async def get_feeds_by_language(self, lang: str) -> List[Dict[str, Any]]:
        """Get feeds by language"""
        pass

    @abstractmethod
    async def get_feeds_by_source(self, source_name: str) -> List[Dict[str, Any]]:
        """Get feeds by source name"""
        pass

    @abstractmethod
    async def add_feed(self, url: str, category_name: str, source_name: str, language: str, is_active: bool = True) -> bool:
        """Add new RSS feed"""
        pass

    @abstractmethod
    async def update_feed(self, feed_id: int, **kwargs) -> bool:
        """Update RSS feed"""
        pass

    @abstractmethod
    async def delete_feed(self, feed_id: int) -> bool:
        """Delete RSS feed"""
        pass




class IMediaExtractor(ABC):
    """Interface for media extraction from RSS items"""

    @abstractmethod
    async def extract_image(self, rss_item: Dict[str, Any]) -> Optional[str]:
        """Extract image URL from RSS item"""
        pass

    @abstractmethod
    async def extract_video(self, rss_item: Dict[str, Any]) -> Optional[str]:
        """Extract video URL from RSS item"""
        pass