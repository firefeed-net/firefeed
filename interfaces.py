# interfaces.py - Base interfaces and abstractions for FireFeed
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Protocol, Union, Callable, Awaitable
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

    @abstractmethod
    async def fetch_unprocessed_rss_items(self) -> List[Dict[str, Any]]:
        """Fetch unprocessed RSS items"""
        pass

    @abstractmethod
    async def get_last_telegram_publication_time(self, feed_id: int) -> Optional[datetime]:
        """Get last Telegram publication time for feed"""
        pass

    @abstractmethod
    async def get_recent_telegram_publications_count(self, feed_id: int, minutes: int) -> int:
        """Get count of recent Telegram publications for feed"""
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


class IModelManager(ABC):
    """Interface for ML model management"""

    @abstractmethod
    async def get_model(self, source_lang: str, target_lang: str) -> Tuple[Any, Any]:
        """Get model and tokenizer for translation direction"""
        pass

    @abstractmethod
    async def preload_popular_models(self) -> None:
        """Preload commonly used models"""
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear model cache"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get model cache statistics"""
        pass


class ITranslationService(ABC):
    """Interface for text translation operations"""

    @abstractmethod
    async def translate_async(self, texts: List[str], source_lang: str, target_lang: str,
                            context_window: int = 2, beam_size: Optional[int] = None) -> List[str]:
        """Translate texts asynchronously"""
        pass

    @abstractmethod
    async def prepare_translations(self, title: str, content: str, original_lang: str,
                                 target_langs: List[str]) -> Dict[str, Dict[str, str]]:
        """Prepare translations for title and content to multiple languages"""
        pass


class ITranslationCache(ABC):
    """Interface for translation caching"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached translation"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> None:
        """Set cached translation with TTL"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached translations"""
        pass


class IDuplicateDetector(ABC):
    """Interface for duplicate content detection"""

    @abstractmethod
    async def is_duplicate(self, title: str, content: str, link: str, lang: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if content is duplicate"""
        pass

    @abstractmethod
    async def process_rss_item(self, rss_item_id: str, title: str, content: str, lang_code: str) -> bool:
        """Process RSS item for duplicate detection and embedding generation"""
        pass


class ILogger(ABC):
    """Interface for logging operations"""

    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def critical(self, message: str, *args, **kwargs) -> None:
        pass


class IDatabasePool(ABC):
    """Interface for database connection pool"""

    @abstractmethod
    async def acquire(self):
        """Acquire database connection"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close pool"""
        pass


class ITranslatorQueue(ABC):
    """Interface for translation task queue"""

    @abstractmethod
    async def add_task(self, title: str, content: str, original_lang: str,
                      callback=None, error_callback=None, task_id=None) -> None:
        """Add translation task to queue"""
        pass

    @abstractmethod
    async def wait_completion(self) -> None:
        """Wait for all tasks to complete"""
        pass

    @abstractmethod
    def print_stats(self) -> None:
        """Print queue statistics"""
        pass


class IMaintenanceService(ABC):
    """Interface for maintenance operations"""

    @abstractmethod
    async def cleanup_duplicates(self) -> None:
        """Clean up duplicate RSS items"""
        pass


# --- User Service Interfaces ---

class ITelegramUserService(ABC):
    """Interface for Telegram bot user management"""

    @abstractmethod
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings (subscriptions, language)"""
        pass

    @abstractmethod
    async def save_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save user settings"""
        pass

    @abstractmethod
    async def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set user language"""
        pass

    @abstractmethod
    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Get user subscriptions only"""
        pass

    @abstractmethod
    async def get_user_language(self, user_id: int) -> str:
        """Get user language only"""
        pass

    @abstractmethod
    async def get_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for category"""
        pass

    @abstractmethod
    async def get_all_users(self) -> List[int]:
        """Get all users"""
        pass


class IWebUserService(ABC):
    """Interface for web user management and Telegram linking"""

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
        """Get web user by Telegram ID"""
        pass

    @abstractmethod
    async def unlink_telegram(self, user_id: int) -> bool:
        """Unlink Telegram account"""
        pass


class IUserManager(ABC):
    """Interface for backward compatibility user manager"""

    @abstractmethod
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        pass

    @abstractmethod
    async def save_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save user settings"""
        pass

    @abstractmethod
    async def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set user language"""
        pass

    @abstractmethod
    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Get user subscriptions"""
        pass

    @abstractmethod
    async def get_user_language(self, user_id: int) -> str:
        """Get user language"""
        pass

    @abstractmethod
    async def get_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for category"""
        pass

    @abstractmethod
    async def get_all_users(self) -> List[int]:
        """Get all users"""
        pass

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
        """Unlink Telegram"""
        pass