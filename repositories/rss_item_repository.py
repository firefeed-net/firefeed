# repositories/rss_item_repository.py - RSS item repository implementation
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from interfaces import IRSSItemRepository
from exceptions import DatabaseException

logger = logging.getLogger(__name__)


class RSSItemRepository(IRSSItemRepository):
    """PostgreSQL implementation of RSS item repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool


    async def get_all_rss_items_list(self, limit: int, offset: int, category_id: Optional[List[int]] = None,
                                     source_id: Optional[List[int]] = None, from_date: Optional[datetime] = None,
                                     display_language: Optional[str] = None, original_language: Optional[str] = None,
                                     search_phrase: Optional[str] = None, before_created_at: Optional[datetime] = None,
                                     cursor_news_id: Optional[str] = None, telegram_published: Optional[bool] = None,
                                     telegram_channels_published: Optional[bool] = None, telegram_users_published: Optional[bool] = None) -> Tuple[int, List[Dict[str, Any]], List[str]]:

        # Build query dynamically
        base_query = """
            SELECT
                pnd.news_id,
                pnd.original_title,
                pnd.original_content,
                pnd.original_language,
                pnd.image_filename,
                c.name as category_name,
                s.name as source_name,
                s.alias as source_alias,
                pnd.source_url,
                pnd.created_at,
                pnd.rss_feed_id as rss_feed_id,
                nt_ru.translated_title as title_ru,
                nt_ru.translated_content as content_ru,
                nt_de.translated_title as title_de,
                nt_de.translated_content as content_de,
                nt_fr.translated_title as title_fr,
                nt_fr.translated_content as content_fr,
                nt_en.translated_title as title_en,
                nt_en.translated_content as content_en
            FROM published_news_data pnd
            JOIN categories c ON pnd.category_id = c.id
            LEFT JOIN rss_feeds rf ON pnd.rss_feed_id = rf.id
            LEFT JOIN sources s ON rf.source_id = s.id
            LEFT JOIN news_translations nt_ru ON pnd.news_id = nt_ru.news_id AND nt_ru.language = 'ru'
            LEFT JOIN news_translations nt_de ON pnd.news_id = nt_de.news_id AND nt_de.language = 'de'
            LEFT JOIN news_translations nt_fr ON pnd.news_id = nt_fr.news_id AND nt_fr.language = 'fr'
            LEFT JOIN news_translations nt_en ON pnd.news_id = nt_en.news_id AND nt_en.language = 'en'
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
            conditions.append("s.id = ANY(%s)")
            params.append(source_id)

        if from_date:
            conditions.append("pnd.created_at >= %s")
            params.append(from_date)

        if before_created_at:
            conditions.append("pnd.created_at < %s")
            params.append(before_created_at)

        # Telegram publication filters
        if telegram_published is not None:
            if telegram_published:
                conditions.append("EXISTS (SELECT 1 FROM rss_items_telegram_bot_published rtp WHERE rtp.news_id = pnd.news_id)")
            else:
                conditions.append("NOT EXISTS (SELECT 1 FROM rss_items_telegram_bot_published rtp WHERE rtp.news_id = pnd.news_id)")

        if telegram_channels_published is not None:
            if telegram_channels_published:
                conditions.append("EXISTS (SELECT 1 FROM rss_items_telegram_bot_published rtp WHERE rtp.news_id = pnd.news_id AND rtp.recipient_type = 'channel')")
            else:
                conditions.append("NOT EXISTS (SELECT 1 FROM rss_items_telegram_bot_published rtp WHERE rtp.news_id = pnd.news_id AND rtp.recipient_type = 'channel')")

        if telegram_users_published is not None:
            if telegram_users_published:
                conditions.append("EXISTS (SELECT 1 FROM rss_items_telegram_bot_published rtp WHERE rtp.news_id = pnd.news_id AND rtp.recipient_type = 'user')")
            else:
                conditions.append("NOT EXISTS (SELECT 1 FROM rss_items_telegram_bot_published rtp WHERE rtp.news_id = pnd.news_id AND rtp.recipient_type = 'user')")

        where_clause = " AND ".join(conditions) if conditions else ""
        if where_clause:
            base_query += f" AND {where_clause}"

        base_query += " ORDER BY pnd.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(base_query, params)
                    results = await cur.fetchall()
                    columns = [desc[0] for desc in cur.description]

                    # Get total count
                    count_query = f"""
                        SELECT COUNT(*) FROM published_news_data pnd
                        JOIN categories c ON pnd.category_id = c.id
                        LEFT JOIN rss_feeds rf ON pnd.rss_feed_id = rf.id
                        LEFT JOIN sources s ON rf.source_id = s.id
                        WHERE 1=1
                    """
                    if where_clause:
                        count_query += f" AND {where_clause}"

                    await cur.execute(count_query, params[:-2])  # Remove limit and offset
                    total_count = (await cur.fetchone())[0]

                    return total_count, results, columns
                except Exception as e:
                    raise DatabaseException(f"Failed to get all RSS items list: {str(e)}")

    async def get_user_rss_items_list(self, user_id: int, display_language: Optional[str],
                                      original_language: Optional[str], limit: int, offset: int) -> Tuple[int, List[Tuple], List[str]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 1. Get IDs of categories the user is subscribed to
                    user_categories = await self._get_user_categories(user_id)
                    user_category_ids = [cat["id"] for cat in user_categories]

                    # If user has no subscriptions, return empty result
                    if not user_category_ids:
                        return 0, [], []

                    # 2. Get IDs of user's RSS feeds from these categories
                    await cur.execute(
                        """
                        SELECT id FROM user_rss_feeds
                        WHERE user_id = %s AND category_id = ANY(%s) AND is_active = TRUE
                        """,
                        (user_id, user_category_ids),
                    )
                    user_rss_feed_ids = [row[0] for row in await cur.fetchall()]

                    # If no active feeds in subscribed categories, return empty result
                    if not user_rss_feed_ids:
                        return 0, [], []

                    # 3. Count total number of RSS items for pagination
                    count_query = """
                    SELECT COUNT(*)
                    FROM published_news_data nd
                    WHERE nd.rss_feed_id = ANY(%s) -- Filter by user RSS feeds
                    """
                    count_params = [user_rss_feed_ids]

                    # Add filters for counting
                    if original_language:
                        count_query += " AND nd.original_language = %s"
                        count_params.append(original_language)

                    await cur.execute(count_query, count_params)
                    total_count = await cur.fetchone()
                    total_count = total_count[0] if total_count else 0

                    # 4. Getting the RSS items themselves with JOINs
                    query_params = []

                    query = """
                    SELECT
                    nd.*,
                    COALESCE(c.name, 'Unknown Category') AS category_name,
                    COALESCE(s.name, 'Unknown Source') AS source_name,
                    nd.source_url as source_url, -- Get original news URL from published_news_data
                    nd.created_at as published_at, -- Use created_at from published_news_data as published_at
                    nt_ru.translated_title as title_ru,
                    nt_ru.translated_content as content_ru,
                    nt_en.translated_title as title_en,
                    nt_en.translated_content as content_en,
                    nt_de.translated_title as title_de,
                    nt_de.translated_content as content_de,
                    nt_fr.translated_title as title_fr,
                    nt_fr.translated_content as content_fr,
                    nt_display.translated_title as display_title,
                    nt_display.translated_content as display_content
                    FROM published_news_data nd
                    LEFT JOIN rss_feeds rf ON nd.rss_feed_id = rf.id
                    LEFT JOIN categories c ON nd.category_id = c.id
                    LEFT JOIN sources s ON rf.source_id = s.id
                    LEFT JOIN news_translations nt_ru ON nd.news_id = nt_ru.news_id AND nt_ru.language = %s
                    LEFT JOIN news_translations nt_en ON nd.news_id = nt_en.news_id AND nt_en.language = %s
                    LEFT JOIN news_translations nt_de ON nd.news_id = nt_de.news_id AND nt_de.language = %s
                    LEFT JOIN news_translations nt_fr ON nd.news_id = nt_fr.news_id AND nt_fr.language = %s
                    LEFT JOIN news_translations nt_display ON nd.news_id = nt_display.news_id AND nt_display.language = %s
                    WHERE nd.rss_feed_id = ANY(%s) -- Filter by user RSS feeds
                    """

                    # Add parameters for language JOINs
                    query_params.extend(["ru", "en", "de", "fr", display_language or "en", user_rss_feed_ids])

                    # Add filters to WHERE
                    if original_language:
                        query += " AND nd.original_language = %s"
                        query_params.append(original_language)

                    # Add ORDER BY, LIMIT and OFFSET
                    # Use created_at from published_news_data for sorting
                    query += " ORDER BY nd.created_at DESC LIMIT %s OFFSET %s"
                    query_params.append(limit)
                    query_params.append(offset)

                    await cur.execute(query, query_params)
                    results = []
                    async for row in cur:
                        results.append(row)

                    # Get column names
                    columns = [desc[0] for desc in cur.description]

                    return total_count, results, columns

                except Exception as e:
                    raise DatabaseException(f"Failed to get user RSS items list for user {user_id}: {str(e)}")

    async def get_user_rss_items_list_by_feed(self, user_id: int, feed_id: str, display_language: Optional[str], original_language: Optional[str], limit: int, offset: int) -> Tuple[int, List[Tuple], List[str]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # 1. Check if feed belongs to user and is active
                    await cur.execute(
                        """
                        SELECT 1 FROM user_rss_feeds
                        WHERE id = %s AND user_id = %s AND is_active = TRUE
                        """,
                        (feed_id, user_id),
                    )
                    feed_exists = await cur.fetchone()

                    if not feed_exists:
                        # Here we return 0, [] for consistency with other functions
                        return 0, [], []

                    # 2. Count total number of RSS items for pagination
                    count_query = """
                    SELECT COUNT(*)
                    FROM published_news_data nd
                    WHERE nd.rss_feed_id = %s -- Filter by specific user RSS feed
                    """
                    count_params = [feed_id]

                    # Add filters for counting
                    if original_language:
                        count_query += " AND nd.original_language = %s"
                        count_params.append(original_language)

                    await cur.execute(count_query, count_params)
                    total_count = await cur.fetchone()
                    total_count = total_count[0] if total_count else 0

                    # 3. Getting the RSS items themselves with JOINs
                    query_params = []

                    query = """
                    SELECT
                    nd.*,
                    COALESCE(c.name, 'Unknown Category') AS category_name,
                    COALESCE(s.name, 'Unknown Source') AS source_name,
                    nd.source_url as source_url, -- Get original news URL from published_news_data
                    nd.created_at as created_at, -- Use created_at from published_news_data
                    nt_ru.translated_title as title_ru,
                    nt_ru.translated_content as content_ru,
                    nt_en.translated_title as title_en,
                    nt_en.translated_content as content_en,
                    nt_de.translated_title as title_de,
                    nt_de.translated_content as content_de,
                    nt_fr.translated_title as title_fr,
                    nt_fr.translated_content as content_fr,
                    nt_display.translated_title as display_title,
                    nt_display.translated_content as display_content
                    FROM published_news_data nd
                    LEFT JOIN rss_feeds rf ON nd.rss_feed_id = rf.id
                    LEFT JOIN categories c ON nd.category_id = c.id
                    LEFT JOIN sources s ON rf.source_id = s.id
                    LEFT JOIN news_translations nt_ru ON nd.news_id = nt_ru.news_id AND nt_ru.language = %s
                    LEFT JOIN news_translations nt_en ON nd.news_id = nt_en.news_id AND nt_en.language = %s
                    LEFT JOIN news_translations nt_de ON nd.news_id = nt_de.news_id AND nt_de.language = %s
                    LEFT JOIN news_translations nt_fr ON nd.news_id = nt_fr.news_id AND nt_fr.language = %s
                    LEFT JOIN news_translations nt_display ON nd.news_id = nt_display.news_id AND nt_display.language = %s
                    WHERE nd.rss_feed_id = %s -- Filter by specific user RSS feed
                    """

                    # Add parameters for language JOINs
                    query_params.extend(["ru", "en", "de", "fr", display_language or "en", feed_id])

                    # Add filters to WHERE
                    if original_language:
                        query += " AND nd.original_language = %s"
                        query_params.append(original_language)

                    # Add ORDER BY, LIMIT and OFFSET
                    # Use created_at from published_news_data for sorting
                    query += " ORDER BY nd.created_at DESC LIMIT %s OFFSET %s"
                    query_params.append(limit)
                    query_params.append(offset)

                    await cur.execute(query, query_params)
                    results = []
                    async for row in cur:
                        results.append(row)

                    # Get column names
                    columns = [desc[0] for desc in cur.description]

                    return total_count, results, columns

                except Exception as e:
                    raise DatabaseException(f"Failed to get user RSS items list by feed {feed_id} for user {user_id}: {str(e)}")

    async def _get_user_categories(self, user_id: int) -> List[Dict[str, Any]]:
        """Helper method to get user categories"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT category_id FROM user_categories WHERE user_id = %s",
                    (user_id,)
                )
                categories = []
                async for row in cur:
                    categories.append({"id": row[0]})
                return categories

    async def get_rss_item_by_id_full(self, rss_item_id: str) -> Optional[Tuple[Tuple, List[str]]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    query = """
                        SELECT
                            pnd.news_id,
                            pnd.original_title,
                            pnd.original_content,
                            pnd.original_language,
                            pnd.image_filename,
                            c.name as category_name,
                            s.name as source_name,
                            s.alias as source_alias,
                            pnd.source_url,
                            pnd.created_at,
                            pnd.embedding,
                            nt_ru.translated_title as title_ru,
                            nt_ru.translated_content as content_ru,
                            nt_de.translated_title as title_de,
                            nt_de.translated_content as content_de,
                            nt_fr.translated_title as title_fr,
                            nt_fr.translated_content as content_fr,
                            nt_en.translated_title as title_en,
                            nt_en.translated_content as content_en
                        FROM published_news_data pnd
                        JOIN categories c ON pnd.category_id = c.id
                        LEFT JOIN rss_feeds rf ON pnd.rss_feed_id = rf.id
                        LEFT JOIN sources s ON rf.source_id = s.id
                        LEFT JOIN news_translations nt_ru ON pnd.news_id = nt_ru.news_id AND nt_ru.language = 'ru'
                        LEFT JOIN news_translations nt_de ON pnd.news_id = nt_de.news_id AND nt_de.language = 'de'
                        LEFT JOIN news_translations nt_fr ON pnd.news_id = nt_fr.news_id AND nt_fr.language = 'fr'
                        LEFT JOIN news_translations nt_en ON pnd.news_id = nt_en.news_id AND nt_en.language = 'en'
                        WHERE pnd.news_id = %s
                    """
                    await cur.execute(query, (rss_item_id,))
                    result = await cur.fetchone()
                    if result:
                        columns = [desc[0] for desc in cur.description]
                        return result, columns
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get RSS item by ID {rss_item_id}: {str(e)}")

    async def get_recent_rss_items_for_broadcast(self, last_check_time: datetime) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
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
                except Exception as e:
                    raise DatabaseException(f"Failed to get recent RSS items for broadcast: {str(e)}")

    # Duplicate detection methods
    async def get_embedding_by_news_id(self, news_id: str) -> Optional[List[float]]:
        """Get embedding by news ID"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
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
                except Exception as e:
                    raise DatabaseException(f"Failed to get embedding by news ID {news_id}: {str(e)}")

    async def save_embedding(self, news_id: str, embedding: List[float]) -> bool:
        """Save embedding for news item"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        """
                        UPDATE published_news_data
                        SET embedding = %s
                        WHERE news_id = %s
                        """,
                        (embedding, news_id)
                    )
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to save embedding for news ID {news_id}: {str(e)}")

    async def get_similar_rss_items_by_embedding(self, embedding: List[float], exclude_news_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get similar RSS items by embedding using vector similarity"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
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
                except Exception as e:
                    raise DatabaseException(f"Failed to get similar RSS items by embedding: {str(e)}")
        
            async def cleanup_old_rss_items(self, hours_old: int) -> Tuple[int, List[Tuple[str, str]], bool]:
                """Atomic cleanup of RSS items older than the specified number of hours and all related data

                Returns:
                    Tuple[int, List[Tuple[str, str]], bool]:
                    (number of deleted news items, list of files to delete (image, video), operation success)
                """
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_old)

                async with self.db_pool.acquire() as conn:
                    async with conn.transaction():  # Atomic transaction
                        try:
                            async with conn.cursor() as cur:
                                # 1. Get list of image and video files to delete BEFORE deleting records
                                await cur.execute("""
                                    SELECT image_filename, video_filename
                                    FROM published_news_data
                                    WHERE created_at < %s AND (image_filename IS NOT NULL OR video_filename IS NOT NULL)
                                """, (cutoff_time,))

                                files_to_delete = await cur.fetchall()

                                # 2. Delete Telegram publication records (linked by news_id)
                                await cur.execute("""
                                    DELETE FROM rss_items_telegram_bot_published
                                    WHERE news_id IN (
                                        SELECT news_id FROM published_news_data WHERE created_at < %s
                                    )
                                """, (cutoff_time,))

                                # 3. Delete news translations
                                await cur.execute("""
                                    DELETE FROM news_translations
                                    WHERE news_id IN (
                                        SELECT news_id FROM published_news_data WHERE created_at < %s
                                    )
                                """, (cutoff_time,))

                                # 4. Delete the news items themselves (published_news_data) - last step
                                await cur.execute("""
                                    DELETE FROM published_news_data
                                    WHERE created_at < %s
                                """, (cutoff_time,))

                                deleted_count = cur.rowcount

                                logger.info(f"[CLEANUP] Transaction successful: deleted {deleted_count} old RSS items older than {hours_old} hours")

                                return deleted_count, files_to_delete, True

                        except Exception as e:
                            logger.error(f"[CLEANUP] Error in cleanup transaction: {e}")
                            raise  # Automatic rollback of transaction

    async def check_duplicate_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if URL already exists in published news"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
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
                except Exception as e:
                    raise DatabaseException(f"Failed to check duplicate by URL {url}: {str(e)}")

    async def get_rss_items_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get RSS items without embeddings for batch processing"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
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
                except Exception as e:
                    raise DatabaseException(f"Failed to get RSS items without embeddings: {str(e)}")