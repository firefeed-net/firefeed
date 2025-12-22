# interfaces/repository_interfaces.py - Repository interfaces
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class IRSSFeedRepository(ABC):
    """Interface for RSS feed repository"""

    @abstractmethod
    async def create_user_rss_feed(self, user_id: int, url: str, name: str, category_id: int, language: str) -> Optional[Dict[str, Any]]:
        """Create user RSS feed"""
        pass

    @abstractmethod
    async def get_user_rss_feeds(self, user_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get user RSS feeds"""
        pass

    @abstractmethod
    async def get_user_rss_feed_by_id(self, user_id: int, feed_id: str) -> Optional[Dict[str, Any]]:
        """Get user RSS feed by ID"""
        pass

    @abstractmethod
    async def update_user_rss_feed(self, user_id: int, feed_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user RSS feed"""
        pass

    @abstractmethod
    async def delete_user_rss_feed(self, user_id: int, feed_id: str) -> bool:
        """Delete user RSS feed"""
        pass

    @abstractmethod
    async def get_all_active_feeds(self) -> List[Dict[str, Any]]:
        """Get all active system RSS feeds"""
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


class IRSSItemRepository(ABC):
    """Interface for RSS item repository"""

    @abstractmethod
    async def save_rss_item(self, rss_item: Dict[str, Any], feed_id: int) -> Optional[str]:
        """Save RSS item to database"""
        pass

    @abstractmethod
    async def get_all_rss_items_list(self, limit: int, offset: int, category_id: Optional[List[int]] = None,
                                    source_id: Optional[List[int]] = None, from_date: Optional[datetime] = None,
                                    display_language: Optional[str] = None, original_language: Optional[str] = None,
                                    search_phrase: Optional[str] = None, before_created_at: Optional[datetime] = None,
                                    cursor_news_id: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]], List[str]]:
        """Get all RSS items list"""
        pass

    @abstractmethod
    async def get_user_rss_items_list(self, user_id: int, display_language: Optional[str],
                                     original_language: Optional[str], limit: int, offset: int) -> Tuple[int, List[Dict[str, Any]], List[str]]:
        """Get user RSS items list"""
        pass

    @abstractmethod
    async def get_rss_item_by_id_full(self, rss_item_id: str) -> Optional[Tuple]:
        """Get RSS item by ID with full data"""
        pass

    @abstractmethod
    async def get_recent_rss_items_for_broadcast(self, last_check_time: datetime) -> List[Dict[str, Any]]:
        """Get recent RSS items for broadcast"""
        pass

    # Duplicate detection methods
    @abstractmethod
    async def get_embedding_by_news_id(self, news_id: str) -> Optional[List[float]]:
        """Get embedding by news ID"""
        pass

    @abstractmethod
    async def save_embedding(self, news_id: str, embedding: List[float]) -> bool:
        """Save embedding for news item"""
        pass

    @abstractmethod
    async def get_similar_rss_items_by_embedding(self, embedding: List[float], exclude_news_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get similar RSS items by embedding"""
        pass

    @abstractmethod
    async def check_duplicate_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if URL already exists"""
        pass

    @abstractmethod
    async def get_rss_items_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get RSS items without embeddings"""
        pass


class ICategoryRepository(ABC):
    """Interface for category repository"""

    @abstractmethod
    async def get_user_categories(self, user_id: int, source_ids: List[int]) -> List[Dict[str, Any]]:
        """Get user categories"""
        pass

    @abstractmethod
    async def update_user_categories(self, user_id: int, category_ids: List[int]) -> bool:
        """Update user categories"""
        pass

    @abstractmethod
    async def get_all_category_ids(self) -> List[int]:
        """Get all category IDs"""
        pass

    @abstractmethod
    async def get_category_id_by_name(self, category_name: str) -> Optional[int]:
        """Get category ID by name"""
        pass

    @abstractmethod
    async def get_all_categories_list(self, limit: int, offset: int, source_ids: List[int]) -> Tuple[int, List[Dict[str, Any]]]:
        """Get all categories list"""
        pass


class ISourceRepository(ABC):
    """Interface for source repository"""

    @abstractmethod
    async def get_source_id_by_alias(self, source_alias: str) -> Optional[int]:
        """Get source ID by alias"""
        pass

    @abstractmethod
    async def get_all_sources_list(self, limit: int, offset: int, category_ids: List[int]) -> Tuple[int, List[Dict[str, Any]]]:
        """Get all sources list"""
        pass


class IApiKeyRepository(ABC):
    """Interface for API key repository"""

    @abstractmethod
    async def create_user_api_key(self, user_id: int, key: str, limits: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create user API key"""
        pass

    @abstractmethod
    async def get_user_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user API keys"""
        pass

    @abstractmethod
    async def get_user_api_key_by_id(self, user_id: int, key_id: int) -> Optional[Dict[str, Any]]:
        """Get user API key by ID"""
        pass

    @abstractmethod
    async def update_user_api_key(self, user_id: int, key_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user API key"""
        pass

    @abstractmethod
    async def delete_user_api_key(self, user_id: int, key_id: int) -> bool:
        """Delete user API key"""
        pass

    @abstractmethod
    async def get_user_api_key_by_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get user API key by key value"""
        pass

