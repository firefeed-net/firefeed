# telegram_bot/services/database_service.py - Database operations for Telegram bot
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from di_container import get_service
from interfaces import ITelegramRepository

logger = logging.getLogger(__name__)


async def mark_bot_published(news_id: str = None, translation_id: int = None, recipient_type: str = 'channel', recipient_id: int = None, message_id: int = None, language: str = None):
    """Marks publication in unified Telegram bot table (channels and users)."""
    try:
        # Convert recipient_id to int if it's a string (for channels)
        if isinstance(recipient_id, str):
            recipient_id = int(recipient_id)
        telegram_repo = get_service(ITelegramRepository)
        result = await telegram_repo.mark_bot_published(news_id, translation_id, recipient_type, recipient_id, message_id, language)
        logger.info(f"Marked as published: news_id={news_id}, translation_id={translation_id}, type={recipient_type}, recipient={recipient_id}")
        return result
    except Exception as e:
        logger.error(f"Error marking bot publication: {e}")
        return False


async def check_bot_published(news_id: str = None, translation_id: int = None, recipient_type: str = 'channel', recipient_id: int = None) -> bool:
    """Checks if item was already published to recipient."""
    try:
        # Convert recipient_id to int if it's a string (for channels)
        if isinstance(recipient_id, str):
            recipient_id = int(recipient_id)
        telegram_repo = get_service(ITelegramRepository)
        return await telegram_repo.check_bot_published(news_id, translation_id, recipient_type, recipient_id)
    except Exception as e:
        logger.error(f"Error checking bot publication: {e}")
        return False


# Legacy functions for backward compatibility (redirect to new unified functions)
async def mark_translation_as_published(translation_id: int, channel_id: int, message_id: int = None):
    """Legacy: Marks translation as published in Telegram channel."""
    # Get news_id from translation
    news_id = await get_news_id_from_translation(translation_id)
    return await mark_bot_published(news_id=news_id, translation_id=translation_id, recipient_type='channel', recipient_id=channel_id, message_id=message_id)


async def get_news_id_from_translation(translation_id: int) -> str:
    """Helper to get news_id from translation_id."""
    try:
        telegram_repo = get_service(ITelegramRepository)
        return await telegram_repo.get_news_id_from_translation(translation_id)
    except Exception as e:
        logger.error(f"Error getting news_id from translation {translation_id}: {e}")
        return None


# Legacy function for backward compatibility
async def mark_original_as_published(news_id: str, channel_id: int, message_id: int = None):
    """Legacy: Marks original news as published in Telegram channel."""
    return await mark_bot_published(news_id=news_id, translation_id=None, recipient_type='channel', recipient_id=channel_id, message_id=message_id)


async def get_translation_id(news_id: str, language: str) -> int:
    """Gets translation ID from news_translations table."""
    try:
        telegram_repo = get_service(ITelegramRepository)
        return await telegram_repo.get_translation_id(news_id, language)
    except Exception as e:
        logger.error(f"Error getting translation ID for {news_id} in {language}: {e}")
        return None


async def get_feed_cooldown_and_max_news(feed_id: int) -> tuple[int, int]:
    """Gets cooldown minutes and max news per hour for feed."""
    try:
        telegram_repo = get_service(ITelegramRepository)
        return await telegram_repo.get_feed_cooldown_and_max_news(feed_id)
    except Exception as e:
        logger.error(f"Error getting cooldown and max_news for feed {feed_id}: {e}")
        return (60, 10)


async def get_last_telegram_publication_time(feed_id: int) -> Optional[datetime]:
    """Get last Telegram publication time for feed from unified table."""
    try:
        telegram_repo = get_service(ITelegramRepository)
        return await telegram_repo.get_last_telegram_publication_time(feed_id)
    except Exception as e:
        logger.error(f"Error getting last Telegram publication time for feed {feed_id}: {e}")
        return None


async def get_recent_telegram_publications_count(feed_id: int, minutes: int) -> int:
    """Get count of recent Telegram publications for feed from unified table."""
    try:
        telegram_repo = get_service(ITelegramRepository)
        return await telegram_repo.get_recent_telegram_publications_count(feed_id, minutes)
    except Exception as e:
        logger.error(f"Error getting recent Telegram publications count for feed {feed_id}: {e}")
        return 0