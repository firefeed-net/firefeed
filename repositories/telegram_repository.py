# repositories/telegram_repository.py - Telegram repository implementation
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from interfaces import ITelegramRepository

logger = logging.getLogger(__name__)


class TelegramRepository(ITelegramRepository):
    """PostgreSQL implementation of Telegram repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_telegram_link_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT telegram_id, linked_at FROM user_telegram_links WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    return {"telegram_id": row[0], "linked_at": row[1]}
        return None

    async def mark_bot_published(self, news_id: str = None, translation_id: int = None,
                                recipient_type: str = 'channel', recipient_id: int = None,
                                message_id: int = None, language: str = None) -> bool:
        """Marks publication in unified Telegram bot table (channels and users)."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # First check if exists
                check_query = """
                    SELECT id FROM rss_items_telegram_bot_published
                    WHERE news_id = %s AND ((translation_id = %s) OR (translation_id IS NULL AND %s IS NULL)) AND recipient_type = %s AND recipient_id = %s
                """
                await cur.execute(check_query, (news_id, translation_id, translation_id, recipient_type, recipient_id))
                existing = await cur.fetchone()

                if existing:
                    # Update existing
                    update_query = """
                        UPDATE rss_items_telegram_bot_published
                        SET message_id = %s, language = %s, sent_at = NOW(), updated_at = NOW()
                        WHERE id = %s
                    """
                    await cur.execute(update_query, (message_id, language, existing[0]))
                else:
                    # Insert new
                    insert_query = """
                        INSERT INTO rss_items_telegram_bot_published
                        (news_id, translation_id, recipient_type, recipient_id, message_id, language, sent_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """
                    await cur.execute(insert_query, (news_id, translation_id, recipient_type, recipient_id, message_id, language))
                return True

    async def check_bot_published(self, news_id: str = None, translation_id: int = None,
                                 recipient_type: str = 'channel', recipient_id: int = None) -> bool:
        """Checks if item was already published to recipient."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT 1 FROM rss_items_telegram_bot_published
                    WHERE news_id = %s AND ((translation_id = %s) OR (translation_id IS NULL AND %s IS NULL)) AND recipient_type = %s AND recipient_id = %s
                """
                await cur.execute(query, (news_id, translation_id, translation_id, recipient_type, recipient_id))
                result = await cur.fetchone()
                return result is not None

    async def get_news_id_from_translation(self, translation_id: int) -> Optional[str]:
        """Helper to get news_id from translation_id."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = "SELECT news_id FROM news_translations WHERE id = %s"
                await cur.execute(query, (translation_id,))
                result = await cur.fetchone()
                return result[0] if result else None

    async def get_translation_id(self, news_id: str, language: str) -> Optional[int]:
        """Gets translation ID from news_translations table."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT id FROM news_translations
                    WHERE news_id = %s AND language = %s
                """
                await cur.execute(query, (news_id, language))
                result = await cur.fetchone()
                return result[0] if result else None

    async def get_feed_cooldown_and_max_news(self, feed_id: int) -> Tuple[int, int]:
        """Gets cooldown minutes and max news per hour for feed."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT COALESCE(cooldown_minutes, 60), COALESCE(max_news_per_hour, 10)
                    FROM rss_feeds WHERE id = %s
                """
                await cur.execute(query, (feed_id,))
                result = await cur.fetchone()
                return (result[0], result[1]) if result else (60, 10)

    async def get_last_telegram_publication_time(self, feed_id: int) -> Optional[datetime]:
        """Get last Telegram publication time for feed from unified table."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
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
                await cur.execute(query, (feed_id,))
                row = await cur.fetchone()
                if row and row[0] and row[0] > datetime(1970, 1, 1, tzinfo=None):
                    return row[0]
                return None

    async def get_recent_telegram_publications_count(self, feed_id: int, minutes: int) -> int:
        """Get count of recent Telegram publications for feed from unified table."""
        from datetime import datetime, timezone, timedelta

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
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
                await cur.execute(query, (feed_id, time_threshold))
                row = await cur.fetchone()
                return row[0] if row else 0