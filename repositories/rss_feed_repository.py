# repositories/rss_feed_repository.py - RSS feed repository implementation
import logging
from typing import List, Dict, Any, Optional
from interfaces import IRSSFeedRepository
from exceptions import DatabaseException

logger = logging.getLogger(__name__)


class RSSFeedRepository(IRSSFeedRepository):
    """PostgreSQL implementation of RSS feed repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def create_user_rss_feed(self, user_id: int, url: str, name: str, category_id: int, language: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")

                try:
                    # Check for duplicate URL for this user
                    await cur.execute(
                        "SELECT id FROM user_rss_feeds WHERE user_id = %s AND url = %s",
                        (user_id, url)
                    )
                    if await cur.fetchone():
                        await cur.execute("ROLLBACK")
                        return {"error": "duplicate"}

                    # Insert new feed
                    await cur.execute(
                        "INSERT INTO user_rss_feeds (user_id, url, name, category_id, language) VALUES (%s, %s, %s, %s, %s) RETURNING id, url, name, category_id, language, is_active, created_at, updated_at",
                        (user_id, url, name, category_id, language)
                    )
                    row = await cur.fetchone()

                    await cur.execute("COMMIT")

                    if row:
                        return {
                            "id": row[0], "url": row[1], "name": row[2],
                            "category_id": row[3], "language": row[4],
                            "is_active": row[5], "created_at": row[6], "updated_at": row[7]
                        }

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise DatabaseException(f"Failed to create user RSS feed: {str(e)}")

        return None

    async def get_user_rss_feeds(self, user_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, url, name, category_id, language, is_active, created_at, updated_at FROM user_rss_feeds WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                        (user_id, limit, offset)
                    )

                    feeds = []
                    rows = await cur.fetchall()
                    for row in rows:
                        feeds.append({
                            "id": row[0], "url": row[1], "name": row[2],
                            "category_id": row[3], "language": row[4],
                            "is_active": row[5], "created_at": row[6], "updated_at": row[7]
                        })

                    return feeds
                except Exception as e:
                    raise DatabaseException(f"Failed to get user RSS feeds: {str(e)}")

    async def get_user_rss_feed_by_id(self, user_id: int, feed_id: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, url, name, category_id, language, is_active, created_at, updated_at FROM user_rss_feeds WHERE user_id = %s AND id = %s",
                        (user_id, feed_id)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "url": row[1], "name": row[2],
                            "category_id": row[3], "language": row[4],
                            "is_active": row[5], "created_at": row[6], "updated_at": row[7]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get user RSS feed by id: {str(e)}")

    async def update_user_rss_feed(self, user_id: int, feed_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)

        query = f"UPDATE user_rss_feeds SET {', '.join(set_parts)}, updated_at = NOW() WHERE user_id = %s AND id = %s RETURNING id, url, name, category_id, language, is_active, created_at, updated_at"
        values.extend([user_id, feed_id])

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "url": row[1], "name": row[2],
                            "category_id": row[3], "language": row[4],
                            "is_active": row[5], "created_at": row[6], "updated_at": row[7]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to update user RSS feed: {str(e)}")

    async def delete_user_rss_feed(self, user_id: int, feed_id: str) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("DELETE FROM user_rss_feeds WHERE user_id = %s AND id = %s", (user_id, feed_id))
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to delete user RSS feed: {str(e)}")

    async def get_all_active_feeds(self) -> List[Dict[str, Any]]:
        """Get all active system RSS feeds"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # Explicitly list fields from rss_feeds
                    query = """
                    SELECT
                        rf.id,
                        rf.url,
                        rf.name,
                        rf.language,
                        rf.source_id,
                        rf.category_id,
                        s.name as source_name, -- Get source name
                        c.name as category_name, -- Get category name
                        rf.cooldown_minutes, -- Can add if needed
                        rf.max_news_per_hour  -- Can add if needed
                    FROM rss_feeds rf
                    JOIN categories c ON rf.category_id = c.id
                    JOIN sources s ON rf.source_id = s.id
                    WHERE rf.is_active = TRUE
                    """
                    await cur.execute(query)
                    feeds = []
                    rows = await cur.fetchall()
                    for row in rows:
                        feeds.append(
                            {
                                "id": row[0],
                                "url": row[1].strip(),
                                "name": row[2],
                                "lang": row[3],
                                "source_id": row[4],
                                "category_id": row[5],
                                "source": row[6],  # s.name
                                "category": row[7] if row[7] else "uncategorized"
                            }
                        )
                    logger.info(f"Found {len(feeds)} active feeds")
                    return feeds
                except Exception as e:
                    raise DatabaseException(f"Failed to get active feeds: {str(e)}")

    async def get_feeds_by_category(self, category_name: str) -> List[Dict[str, Any]]:
        """Get feeds by category name"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    query = """
                    SELECT
                        rf.id,
                        rf.url,
                        rf.name,
                        rf.language,
                        rf.source_id,
                        rf.category_id,
                        s.name as source_name,
                        c.name as category_name
                    FROM rss_feeds rf
                    JOIN categories c ON rf.category_id = c.id
                    JOIN sources s ON rf.source_id = s.id
                    WHERE c.name = %s AND rf.is_active = TRUE
                    """
                    await cur.execute(query, (category_name,))
                    feeds = []
                    rows = await cur.fetchall()
                    for row in rows:
                        feeds.append({
                            "id": row[0],
                            "url": row[1].strip(),
                            "name": row[2],
                            "lang": row[3],
                            "source_id": row[4],
                            "category_id": row[5],
                            "source": row[6],
                            "category": row[7] if row[7] else "uncategorized"
                        })
                    logger.info(f"Found {len(feeds)} feeds for category '{category_name}'")
                    return feeds
                except Exception as e:
                    raise DatabaseException(f"Failed to get feeds by category '{category_name}': {str(e)}")

    async def get_feeds_by_language(self, lang: str) -> List[Dict[str, Any]]:
        """Get feeds by language"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    query = """
                    SELECT
                        rf.id,
                        rf.url,
                        rf.name,
                        rf.language,
                        rf.source_id,
                        rf.category_id,
                        s.name as source_name,
                        c.name as category_name
                    FROM rss_feeds rf
                    JOIN categories c ON rf.category_id = c.id
                    JOIN sources s ON rf.source_id = s.id
                    WHERE rf.language = %s AND rf.is_active = TRUE
                    """
                    await cur.execute(query, (lang,))
                    feeds = []
                    rows = await cur.fetchall()
                    for row in rows:
                        feeds.append({
                            "id": row[0],
                            "url": row[1].strip(),
                            "name": row[2],
                            "lang": row[3],
                            "source_id": row[4],
                            "category_id": row[5],
                            "source": row[6],
                            "category": row[7] if row[7] else "uncategorized"
                        })
                    logger.info(f"Found {len(feeds)} feeds for language '{lang}'")
                    return feeds
                except Exception as e:
                    raise DatabaseException(f"Failed to get feeds by language '{lang}': {str(e)}")

    async def get_feeds_by_source(self, source_name: str) -> List[Dict[str, Any]]:
        """Get feeds by source name"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    query = """
                    SELECT
                        rf.id,
                        rf.url,
                        rf.name,
                        rf.language,
                        rf.source_id,
                        rf.category_id,
                        s.name as source_name,
                        c.name as category_name
                    FROM rss_feeds rf
                    JOIN categories c ON rf.category_id = c.id
                    JOIN sources s ON rf.source_id = s.id
                    WHERE s.name = %s AND rf.is_active = TRUE
                    """
                    await cur.execute(query, (source_name,))
                    feeds = []
                    rows = await cur.fetchall()
                    for row in rows:
                        feeds.append({
                            "id": row[0],
                            "url": row[1].strip(),
                            "name": row[2],
                            "lang": row[3],
                            "source_id": row[4],
                            "category_id": row[5],
                            "source": row[6],
                            "category": row[7] if row[7] else "uncategorized"
                        })
                    logger.info(f"Found {len(feeds)} feeds for source '{source_name}'")
                    return feeds
                except Exception as e:
                    raise DatabaseException(f"Failed to get feeds by source '{source_name}': {str(e)}")