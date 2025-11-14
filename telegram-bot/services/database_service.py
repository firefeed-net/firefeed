import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from ..interfaces.database_interface import IDatabaseService

logger = logging.getLogger(__name__)


class DatabaseService(IDatabaseService):
    """Service for database operations."""

    async def mark_translation_as_published(self, translation_id: int, channel_id: int, message_id: int = None) -> bool:
        """Marks translation as published in Telegram channel."""
        try:
            # Get shared connection pool
            from config import get_shared_db_pool
            db_pool = await get_shared_db_pool()
            async with db_pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    query = """
                        INSERT INTO rss_items_telegram_published
                        (translation_id, channel_id, message_id, published_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (translation_id, channel_id)
                        DO UPDATE SET
                            message_id = EXCLUDED.message_id,
                            published_at = NOW()
                    """
                    await cursor.execute(query, (translation_id, channel_id, message_id))
                    logger.info(f"Translation {translation_id} marked as published in channel {channel_id}")
                    return True
        except Exception as e:
            logger.error(f"Error marking translation {translation_id} as published: {e}")
            return False

    async def mark_original_as_published(self, news_id: str, channel_id: int, message_id: int = None) -> bool:
        """Marks original news as published in Telegram channel."""
        try:
            from config import get_shared_db_pool
            db_pool = await get_shared_db_pool()
            async with db_pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    query = """
                        INSERT INTO rss_items_telegram_published_originals
                        (news_id, channel_id, message_id, created_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (news_id, channel_id)
                        DO UPDATE SET
                            message_id = EXCLUDED.message_id,
                            created_at = NOW()
                    """
                    await cursor.execute(query, (news_id, channel_id, message_id))
                    logger.info(f"Original news {news_id} marked as published in channel {channel_id}")
                    return True
        except Exception as e:
            logger.error(f"Error marking original news {news_id} as published: {e}")
            return False

    async def get_translation_id(self, news_id: str, language: str) -> Optional[int]:
        """Gets translation ID from news_translations table."""
        try:
            from config import get_shared_db_pool
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

    async def get_feed_cooldown_and_max_news(self, feed_id: int) -> Tuple[int, int]:
        """Gets cooldown minutes and max news per hour for feed."""
        try:
            from config import get_shared_db_pool
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

    async def get_last_telegram_publication_time(self, feed_id: int) -> Optional[datetime]:
        """Get last Telegram publication time for feed."""
        try:
            from config import get_shared_db_pool
            db_pool = await get_shared_db_pool()
            async with db_pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Get latest publication time from both tables
                    query = """
                    SELECT GREATEST(
                        COALESCE((
                            SELECT MAX(rtp.published_at)
                            FROM rss_items_telegram_published rtp
                            JOIN news_translations nt ON rtp.translation_id = nt.id
                            JOIN published_news_data pnd ON nt.news_id = pnd.news_id
                            WHERE pnd.rss_feed_id = %s
                        ), '1970-01-01'::timestamp),
                        COALESCE((
                            SELECT MAX(rtpo.created_at)
                            FROM rss_items_telegram_published_originals rtpo
                            JOIN published_news_data pnd ON rtpo.news_id = pnd.news_id
                            WHERE pnd.rss_feed_id = %s
                        ), '1970-01-01'::timestamp)
                    ) as last_time
                    """
                    await cursor.execute(query, (feed_id, feed_id))
                    row = await cursor.fetchone()
                    if row and row[0] and row[0] > datetime(1970, 1, 1, tzinfo=timezone.utc):
                        return row[0]
                    return None
        except Exception as e:
            logger.error(f"Error getting last Telegram publication time for feed {feed_id}: {e}")
            return None

    async def get_recent_telegram_publications_count(self, feed_id: int, minutes: int) -> int:
        """Get count of recent Telegram publications for feed."""
        try:
            from config import get_shared_db_pool
            db_pool = await get_shared_db_pool()
            async with db_pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
                    # Count publications from both tables
                    query = """
                    SELECT COUNT(*) FROM (
                        SELECT rtp.published_at
                        FROM rss_items_telegram_published rtp
                        JOIN news_translations nt ON rtp.translation_id = nt.id
                        JOIN published_news_data pnd ON nt.news_id = pnd.news_id
                        WHERE pnd.rss_feed_id = %s AND rtp.published_at >= %s
                        UNION ALL
                        SELECT rtpo.created_at as published_at
                        FROM rss_items_telegram_published_originals rtpo
                        JOIN published_news_data pnd ON rtpo.news_id = pnd.news_id
                        WHERE pnd.rss_feed_id = %s AND rtpo.created_at >= %s
                    ) as combined_publications
                    """
                    await cursor.execute(query, (feed_id, time_threshold, feed_id, time_threshold))
                    row = await cursor.fetchone()
                    return row[0] if row else 0
        except Exception as e:
            logger.error(f"Error getting recent Telegram publications count for feed {feed_id}: {e}")
            return 0