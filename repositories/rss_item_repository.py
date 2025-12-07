# repositories/rss_item_repository.py - RSS item repository implementation
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from interfaces import IRSSItemRepository

logger = logging.getLogger(__name__)


class RSSItemRepository(IRSSItemRepository):
    """PostgreSQL implementation of RSS item repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def _get_category_id_by_name(self, category_name: str) -> Optional[int]:
        """Helper method to get category ID by name"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                row = await cur.fetchone()
                return row[0] if row else None

    async def _get_source_id_by_alias(self, source_alias: str) -> Optional[int]:
        """Helper method to get source ID by alias"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM sources WHERE alias = %s", (source_alias,))
                row = await cur.fetchone()
                return row[0] if row else None

    async def get_all_rss_items_list(self, limit: int, offset: int, category_id: Optional[List[int]] = None,
                                    source_id: Optional[List[int]] = None, from_date: Optional[datetime] = None,
                                    display_language: Optional[str] = None, original_language: Optional[str] = None,
                                    search_phrase: Optional[str] = None, before_created_at: Optional[datetime] = None,
                                    cursor_news_id: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]], List[str]]:

        # Build query dynamically
        base_query = """
            SELECT
                pnd.news_id,
                pnd.original_title,
                pnd.original_content,
                pnd.original_language,
                pnd.image_filename,
                c.name as category_name,
                pnd.source_url,
                pnd.created_at
            FROM published_news_data pnd
            JOIN categories c ON pnd.category_id = c.id
            WHERE 1=1
        """

        conditions = []
        params = []

        if original_language:
            conditions.append("pnd.original_language = %s")
            params.append(original_language)

        if category_id:
            conditions.append("pnd.category_id = ANY(%s)")
            params.append(category_id)

        if source_id:
            conditions.append("pnd.source_id = ANY(%s)")
            params.append(source_id)

        if from_date:
            conditions.append("pnd.created_at >= %s")
            params.append(from_date)

        if before_created_at:
            conditions.append("pnd.created_at < %s")
            params.append(before_created_at)

        where_clause = " AND ".join(conditions) if conditions else ""
        if where_clause:
            base_query += f" AND {where_clause}"

        base_query += " ORDER BY pnd.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(base_query, params)
                results = await cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM published_news_data pnd
                    JOIN categories c ON pnd.category_id = c.id
                    WHERE 1=1
                """
                if where_clause:
                    count_query += f" AND {where_clause}"

                await cur.execute(count_query, params[:-2])  # Remove limit and offset
                total_count = (await cur.fetchone())[0]

        return total_count, results, columns

    async def get_user_rss_items_list(self, user_id: int, display_language: Optional[str],
                                     original_language: Optional[str], limit: int, offset: int) -> Tuple[int, List[Dict[str, Any]], List[str]]:
        # Get user's subscribed categories
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Get user's categories
                await cur.execute(
                    "SELECT category_id FROM user_categories WHERE user_id = %s",
                    (user_id,)
                )
                user_categories = [row[0] for row in await cur.fetchall()]

                if not user_categories:
                    return 0, [], []

                # Build query for user's RSS items
                base_query = """
                    SELECT
                        pnd.news_id,
                        pnd.original_title,
                        pnd.original_content,
                        pnd.original_language,
                        pnd.image_filename,
                        c.name as category_name,
                        pnd.source_url,
                        pnd.created_at
                    FROM published_news_data pnd
                    JOIN categories c ON pnd.category_id = c.id
                    WHERE pnd.category_id = ANY(%s)
                """

                conditions = []
                params = [user_categories]

                if original_language:
                    conditions.append("pnd.original_language = %s")
                    params.append(original_language)

                where_clause = " AND ".join(conditions) if conditions else ""
                if where_clause:
                    base_query += f" AND {where_clause}"

                base_query += " ORDER BY pnd.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                await cur.execute(base_query, params)
                results = await cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM published_news_data pnd
                    WHERE pnd.category_id = ANY(%s)
                """
                # No need to join sources since no source_id
                count_params = [user_categories]
                if original_language:
                    count_query += " AND pnd.original_language = %s"
                    count_params.append(original_language)

                await cur.execute(count_query, count_params)
                total_count = (await cur.fetchone())[0]

        return total_count, results, columns

    async def get_rss_item_by_id_full(self, rss_item_id: str) -> Optional[Tuple]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT
                        pnd.news_id,
                        pnd.original_title,
                        pnd.original_content,
                        pnd.original_language,
                        pnd.image_filename,
                        c.name as category_name,
                        pnd.source_url,
                        pnd.created_at,
                        pnd.embedding
                    FROM published_news_data pnd
                    JOIN categories c ON pnd.category_id = c.id
                    WHERE pnd.news_id = %s
                """
                await cur.execute(query, (rss_item_id,))
                result = await cur.fetchone()
                return result

    async def get_recent_rss_items_for_broadcast(self, last_check_time: datetime) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT
                        pnd.news_id,
                        pnd.original_title,
                        pnd.original_content,
                        pnd.original_language,
                        pnd.image_filename,
                        c.name as category_name,
                        pnd.source_url,
                        pnd.created_at
                    FROM published_news_data pnd
                    JOIN categories c ON pnd.category_id = c.id
                    WHERE pnd.created_at > %s
                    ORDER BY pnd.created_at ASC
                """
                await cur.execute(query, (last_check_time,))
                results = await cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                # Convert to list of dicts
                items = []
                for row in results:
                    item = dict(zip(columns, row))
                    # Add default values for missing fields
                    item['source_name'] = 'Unknown'
                    item['source_alias'] = 'unknown'
                    items.append(item)

                return items

    # Duplicate detection methods
    async def get_embedding_by_news_id(self, news_id: str) -> Optional[List[float]]:
        """Get embedding by news ID"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT embedding
                    FROM published_news_data
                    WHERE news_id = %s AND embedding IS NOT NULL
                    """,
                    (news_id,)
                )
                result = await cur.fetchone()
                if result and result[0] is not None:
                    import json
                    if isinstance(result[0], str):
                        return json.loads(result[0])
                    return result[0]
        return None

    async def save_embedding(self, news_id: str, embedding: List[float]) -> bool:
        """Save embedding for news item"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE published_news_data
                    SET embedding = %s
                    WHERE news_id = %s
                    """,
                    (embedding, news_id)
                )
                return cur.rowcount > 0

    async def get_similar_rss_items_by_embedding(self, embedding: List[float], exclude_news_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get similar RSS items by embedding using vector similarity"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                if exclude_news_id:
                    await cur.execute(
                        """
                        SELECT news_id, original_title, original_content, embedding
                        FROM published_news_data
                        WHERE embedding IS NOT NULL AND news_id != %s
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s
                        """,
                        (exclude_news_id, embedding, limit)
                    )
                else:
                    await cur.execute(
                        """
                        SELECT news_id, original_title, original_content, embedding
                        FROM published_news_data
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s
                        """,
                        (embedding, limit)
                    )
                results = await cur.fetchall()
                return [dict(zip([column[0] for column in cur.description], row)) for row in results]

    async def check_duplicate_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if URL already exists in published news"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT news_id, original_title
                    FROM published_news_data
                    WHERE source_url = %s AND source_url IS NOT NULL
                    LIMIT 1
                    """,
                    (url,)
                )
                result = await cur.fetchone()
                if result:
                    return {"news_id": result[0], "title": result[1], "reason": "same_url"}
        return None

    async def get_rss_items_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get RSS items without embeddings for batch processing"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT news_id, original_title, original_content
                    FROM published_news_data
                    WHERE embedding IS NULL
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (limit,)
                )
                results = await cur.fetchall()
                return [dict(zip([column[0] for column in cur.description], row)) for row in results]