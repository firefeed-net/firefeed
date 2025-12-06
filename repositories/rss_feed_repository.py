# repositories/rss_feed_repository.py - RSS feed repository implementation
import logging
from typing import List, Dict, Any, Optional
from interfaces import IRSSFeedRepository

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
                        "INSERT INTO user_rss_feeds (user_id, url, name, category_id, language) VALUES (%s, %s, %s, %s, %s) RETURNING id, url, name, category_id, language, is_active, created_at",
                        (user_id, url, name, category_id, language)
                    )
                    row = await cur.fetchone()

                    await cur.execute("COMMIT")

                    if row:
                        return {
                            "id": str(row[0]), "url": row[1], "name": row[2],
                            "category_id": row[3], "language": row[4],
                            "is_active": row[5], "created_at": row[6]
                        }

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    logger.error(f"Error creating user RSS feed: {e}")

        return None

    async def get_user_rss_feeds(self, user_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, url, name, category_id, language, is_active, created_at FROM user_rss_feeds WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (user_id, limit, offset)
                )

                feeds = []
                async for row in cur:
                    feeds.append({
                        "id": str(row[0]), "url": row[1], "name": row[2],
                        "category_id": row[3], "language": row[4],
                        "is_active": row[5], "created_at": row[6]
                    })

                return feeds

    async def get_user_rss_feed_by_id(self, user_id: int, feed_id: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, url, name, category_id, language, is_active, created_at FROM user_rss_feeds WHERE user_id = %s AND id = %s",
                    (user_id, feed_id)
                )
                row = await cur.fetchone()
                if row:
                    return {
                        "id": str(row[0]), "url": row[1], "name": row[2],
                        "category_id": row[3], "language": row[4],
                        "is_active": row[5], "created_at": row[6]
                    }
        return None

    async def update_user_rss_feed(self, user_id: int, feed_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)

        query = f"UPDATE user_rss_feeds SET {', '.join(set_parts)}, updated_at = NOW() WHERE user_id = %s AND id = %s RETURNING id, url, name, category_id, language, is_active, updated_at"
        values.extend([user_id, feed_id])

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, values)
                row = await cur.fetchone()
                if row:
                    return {
                        "id": str(row[0]), "url": row[1], "name": row[2],
                        "category_id": row[3], "language": row[4],
                        "is_active": row[5], "updated_at": row[6]
                    }
        return None

    async def delete_user_rss_feed(self, user_id: int, feed_id: str) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM user_rss_feeds WHERE user_id = %s AND id = %s", (user_id, feed_id))
                return cur.rowcount > 0