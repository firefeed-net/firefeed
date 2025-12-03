# telegram_bot/services/database_service.py - Database operations for Telegram bot
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from config import get_shared_db_pool

logger = logging.getLogger(__name__)


async def mark_bot_published(news_id: str = None, translation_id: int = None, recipient_type: str = 'channel', recipient_id: int = None, message_id: int = None, language: str = None):
    """Marks publication in unified Telegram bot table (channels and users)."""
    try:
        # Get shared connection pool
        db_pool = await get_shared_db_pool()
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                query = """
                    INSERT INTO rss_items_telegram_bot_published
                    (news_id, translation_id, recipient_type, recipient_id, message_id, language, sent_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (news_id, translation_id, recipient_type, recipient_id)
                    DO UPDATE SET
                        message_id = EXCLUDED.message_id,
                        language = EXCLUDED.language,
                        sent_at = NOW(),
                        updated_at = NOW()
                """
                await cursor.execute(query, (news_id, translation_id, recipient_type, recipient_id, message_id, language))
                logger.info(f"Marked as published: news_id={news_id}, translation_id={translation_id}, type={recipient_type}, recipient={recipient_id}")
                return True
    except Exception as e:
        logger.error(f"Error marking bot publication: {e}")
        return False


async def check_bot_published(news_id: str = None, translation_id: int = None, recipient_type: str = 'channel', recipient_id: int = None) -> bool:
    """Checks if item was already published to recipient."""
    try:
        db_pool = await get_shared_db_pool()
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                query = """
                    SELECT 1 FROM rss_items_telegram_bot_published
                    WHERE news_id = %s AND translation_id = %s AND recipient_type = %s AND recipient_id = %s
                """
                await cursor.execute(query, (news_id, translation_id, recipient_type, recipient_id))
                result = await cursor.fetchone()
                return result is not None
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
        db_pool = await get_shared_db_pool()
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                query = "SELECT news_id FROM news_translations WHERE id = %s"
                await cursor.execute(query, (translation_id,))
                result = await cursor.fetchone()
                return result[0] if result else None
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
        db_pool = await get_shared_db_pool()
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                query = """
                    SELECT id FROM news_translations
                    WHERE news_id = %s AND language = %s
                """
                await cursor.execute(query, (news_id, language))
                result = await cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting translation ID for {news_id} in {language}: {e}")
        return None


async def get_feed_cooldown_and_max_news(feed_id: int) -> tuple[int, int]:
    """Gets cooldown minutes and max news per hour for feed."""
    try:
        db_pool = await get_shared_db_pool()
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                query = """
                    SELECT COALESCE(cooldown_minutes, 60), COALESCE(max_news_per_hour, 10)
                    FROM rss_feeds WHERE id = %s
                """
                await cursor.execute(query, (feed_id,))
                result = await cursor.fetchone()
                return (result[0], result[1]) if result else (60, 10)
    except Exception as e:
        logger.error(f"Error getting cooldown and max_news for feed {feed_id}: {e}")
        return (60, 10)


async def get_last_telegram_publication_time(feed_id: int) -> Optional[datetime]:
    """Get last Telegram publication time for feed from unified table."""
    try:
        db_pool = await get_shared_db_pool()
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                # Get latest publication time from unified table
                query = """
                SELECT MAX(sent_at)
                FROM rss_items_telegram_bot_published rbp
                JOIN published_news_data pnd ON (
                    (rbp.translation_id IS NOT NULL AND rbp.news_id = pnd.news_id) OR
                    (rbp.translation_id IS NULL AND rbp.news_id = pnd.news_id)
                )
                WHERE pnd.rss_feed_id = %s AND rbp.recipient_type = 'channel'
                """
                await cursor.execute(query, (feed_id,))
                row = await cursor.fetchone()
                if row and row[0] and row[0] > datetime(1970, 1, 1, tzinfo=timezone.utc):
                    return row[0]
                return None
    except Exception as e:
        logger.error(f"Error getting last Telegram publication time for feed {feed_id}: {e}")
        return None


async def get_recent_telegram_publications_count(feed_id: int, minutes: int) -> int:
    """Get count of recent Telegram publications for feed from unified table."""
    try:
        db_pool = await get_shared_db_pool()
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
                # Count publications from unified table (only channels)
                query = """
                SELECT COUNT(*)
                FROM rss_items_telegram_bot_published rbp
                JOIN published_news_data pnd ON (
                    (rbp.translation_id IS NOT NULL AND rbp.news_id = pnd.news_id) OR
                    (rbp.translation_id IS NULL AND rbp.news_id = pnd.news_id)
                )
                WHERE pnd.rss_feed_id = %s AND rbp.sent_at >= %s AND rbp.recipient_type = 'channel'
                """
                await cursor.execute(query, (feed_id, time_threshold))
                row = await cursor.fetchone()
                return row[0] if row else 0
    except Exception as e:
        logger.error(f"Error getting recent Telegram publications count for feed {feed_id}: {e}")
        return 0