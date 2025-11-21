# database.py
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set, Tuple

logger = logging.getLogger(__name__)


async def get_db_pool():
    """Getting shared DB pool"""
    try:
        pool = await config.get_shared_db_pool()
        return pool
    except Exception as e:
        logger.info(f"[DB] Error getting PostgreSQL connection pool: {e}")
        return None


async def close_db_pool():
    """Closes the shared database connection pool."""
    try:
        await config.close_shared_db_pool()
        logger.info("[DB] Shared PostgreSQL connection pool closed.")
    except Exception as e:
        logger.info(f"[DB] Error closing PostgreSQL connection pool: {e}")


# --- Functions for working with users ---


async def create_user(pool, email: str, password_hash: str, language: str) -> Optional[Dict[str, Any]]:
    """Creates a new user"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                INSERT INTO users (email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, email, language, is_active, is_verified, is_deleted, created_at, updated_at
                """
                now = datetime.utcnow()
                await cur.execute(query, (email, password_hash, language, False, False, False, now, now))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.info(f"[DB] Error creating user: {e}")
                return None


async def get_user_by_email(pool, email: str) -> Optional[Dict[str, Any]]:
    """Gets user by email"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT id, email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at
                FROM users WHERE email = %s
                """
                await cur.execute(query, (email,))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.info(f"[DB] Error getting user by email: {e}")
                return None


async def get_user_by_id(pool, user_id: int) -> Optional[Dict[str, Any]]:
    """Gets user by ID"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT id, email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at
                FROM users WHERE id = %s
                """
                await cur.execute(query, (user_id,))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.info(f"[DB] Error getting user by id: {e}")
                return None


async def update_user(pool, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates user data"""
    if not update_data:
        return await get_user_by_id(pool, user_id)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                set_parts = []
                params = []
                for key, value in update_data.items():
                    set_parts.append(f"{key} = %s")
                    params.append(value)
                params.append(user_id)

                query = f"""
                UPDATE users
                SET {', '.join(set_parts)}, updated_at = %s
                WHERE id = %s
                RETURNING id, email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at
                """
                params.append(datetime.utcnow())  # updated_at
                await cur.execute(query, params)
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.info(f"[DB] Error updating user: {e}")
                return None


async def delete_user(pool, user_id: int) -> bool:
    """Deactivates (deletes) user"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Instead of physical deletion, deactivate
                query = "UPDATE users SET is_deleted = TRUE, updated_at = %s WHERE id = %s"
                await cur.execute(query, (datetime.utcnow(), user_id))
                # Check if a row was affected
                if cur.rowcount > 0:
                    return True
                return False
            except Exception as e:
                logger.info(f"[DB] Error deleting user: {e}")
                return False


async def activate_user(pool, user_id: int) -> bool:
    """Activates user"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = "UPDATE users SET is_active = TRUE, updated_at = %s WHERE id = %s"
                await cur.execute(query, (datetime.utcnow(), user_id))
                if cur.rowcount > 0:
                    return True
                return False
            except Exception as e:
                logger.info(f"[DB] Error activating user: {e}")
                return False


async def update_user_password(pool, user_id: int, new_hashed_password: str) -> bool:
    """Updates user password"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = "UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s"
                await cur.execute(query, (new_hashed_password, datetime.utcnow(), user_id))
                return cur.rowcount > 0
            except Exception as e:
                logger.error(f"[DB] Error updating user password: {e}")
                return False


# --- Functions for working with verification codes ---


async def save_verification_code(pool, user_id: int, verification_code: str, expires_at: datetime) -> bool:
    """Saves verification code for user according to user_verification_codes schema.
    Fields: (user_id, verification_code, created_at DEFAULT now(), expires_at, used_at NULL)
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Delete old codes for this user (optional cleanup)
                await cur.execute("DELETE FROM user_verification_codes WHERE user_id = %s", (user_id,))
                # Insert new code
                query = """
                INSERT INTO user_verification_codes (user_id, verification_code, expires_at)
                VALUES (%s, %s, %s)
                """
                await cur.execute(query, (user_id, verification_code, expires_at))
                return True
            except Exception as e:
                logger.error(f"[DB] Error saving verification code: {e}")
                return False


async def verify_user_email(pool, email: str, verification_code: str) -> Optional[int]:
    """Verifies verification code and returns user_id if code is valid."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT uvc.user_id
                FROM user_verification_codes uvc
                JOIN users u ON uvc.user_id = u.id
                WHERE u.email = %s
                  AND uvc.verification_code = %s
                  AND uvc.used_at IS NULL
                  AND uvc.expires_at > %s
                """
                await cur.execute(query, (email, verification_code, datetime.utcnow()))
                result = await cur.fetchone()
                if result:
                    return result[0]
                return None
            except Exception as e:
                logger.error(f"[DB] Error verifying user email: {e}")
                return None


async def get_active_verification_code(pool, user_id: int, verification_code: str) -> Optional[dict]:
    """Returns active (unused and not expired) verification code for user."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    """
                    SELECT id, user_id, verification_code, created_at, expires_at, used_at
                    FROM user_verification_codes
                    WHERE user_id = %s AND verification_code = %s AND used_at IS NULL AND expires_at > NOW()
                    FOR UPDATE
                    """,
                    (user_id, verification_code),
                )
                row = await cur.fetchone()
                if row:
                    cols = [d[0] for d in cur.description]
                    return dict(zip(cols, row))
                return None
            except Exception as e:
                logger.error(f"[DB] Error getting active verification code: {e}")
                return None


async def mark_verification_code_used(pool, code_id: int) -> bool:
    """Marks verification code as used (used_at = NOW())."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("UPDATE user_verification_codes SET used_at = NOW() WHERE id = %s", (code_id,))
                return cur.rowcount > 0
            except Exception as e:
                logger.error(f"[DB] Error marking verification code used: {e}")
                return False

# --- Functions for working with password reset tokens ---


async def save_password_reset_token(pool, user_id: int, token: str, expires_at: datetime) -> bool:
    """Saves password reset token"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Delete old tokens for this user
                await cur.execute("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,))
                # Insert new token
                query = """
                INSERT INTO password_reset_tokens (user_id, token, expires_at, created_at)
                VALUES (%s, %s, %s, %s)
                """
                await cur.execute(query, (user_id, token, expires_at, datetime.now(timezone.utc)))
                return True
            except Exception as e:
                logger.info(f"[DB] Error saving password reset token: {e}")
                return False


async def get_password_reset_token(pool, token: str) -> Optional[Dict[str, Any]]:
    """Gets password reset token data if token is valid"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT user_id, expires_at FROM password_reset_tokens
                WHERE token = %s AND expires_at > %s
                """
                await cur.execute(query, (token, datetime.utcnow()))
                result = await cur.fetchone()
                if result:
                    return {"user_id": result[0], "expires_at": result[1]}
                return None
            except Exception as e:
                logger.info(f"[DB] Error getting password reset token: {e}")
                return None


async def delete_password_reset_token(pool, token: str) -> bool:
    """Deletes used password reset token"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
                return True
            except Exception as e:
                logger.error(f"[DB] Error deleting password reset token: {e}")
                return False


# --- Functions for working with user categories ---


async def update_user_categories(pool, user_id: int, category_ids: Set[int]) -> bool:
    """Updates user categories list"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Start transaction
                await cur.execute("BEGIN")

                # Delete all current user categories
                await cur.execute("DELETE FROM user_categories WHERE user_id = %s", (user_id,))

                # Add new categories
                if category_ids:
                    for cat_id in category_ids:
                        await cur.execute(
                            "INSERT INTO user_categories (user_id, category_id) VALUES (%s, %s)", (user_id, cat_id)
                        )

                # Commit transaction
                await cur.execute("COMMIT")
                return True
            except Exception as e:
                await cur.execute("ROLLBACK")
                logger.info(f"[DB] Error updating user categories: {e}")
                return False


async def get_all_category_ids(pool) -> Set[int]:
    """Returns set of all category ids."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("SELECT id FROM categories")
                rows = await cur.fetchall()
                return {row[0] for row in rows}
            except Exception as e:
                logger.error(f"[DB] Error fetching category ids: {e}")
                return set()


async def get_category_id_by_name(pool, category_name: str) -> Optional[int]:
    """Returns category id by its name."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                row = await cur.fetchone()
                return row[0] if row else None
            except Exception as e:
                logger.error(f"[DB] Error fetching category id by name: {e}")
                return None


async def get_source_id_by_alias(pool, source_alias: str) -> Optional[int]:
    """Returns source id by its alias."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("SELECT id FROM sources WHERE alias = %s", (source_alias,))
                row = await cur.fetchone()
                return row[0] if row else None
            except Exception as e:
                logger.error(f"[DB] Error fetching source id by alias: {e}")
                return None

async def get_user_categories(pool, user_id: int, source_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Gets user categories list with filtering by source_id"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT c.id, c.name
                FROM user_categories uc
                JOIN categories c ON uc.category_id = c.id
                WHERE uc.user_id = %s AND c.id != %s
                """
                params = [user_id, config.USER_DEFINED_RSS_CATEGORY_ID]

                if source_ids:
                    placeholders = ",".join(["%s"] * len(source_ids))
                    query += f" AND c.id IN (SELECT category_id FROM source_categories WHERE source_id IN ({placeholders})  AND category_id != %s)"
                    params.extend(source_ids)

                await cur.execute(query, params)
                results = []
                async for row in cur:
                    results.append({"id": row[0], "name": row[1]})
                return results
            except Exception as e:
                logger.info(f"[DB] Error getting user categories: {e}")
                return []


# --- Functions for working with user RSS feeds ---


async def create_user_rss_feed(
    pool, user_id: int, url: str, name: str, category_id: int, language: str
) -> Optional[Dict[str, Any]]:
    """Creates user RSS feed"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Check if the feed already exists for this user
                await cur.execute("SELECT 1 FROM user_rss_feeds WHERE user_id = %s AND url = %s", (user_id, url))
                if await cur.fetchone():
                    return {"error": "duplicate"}

                query = """
                INSERT INTO user_rss_feeds (user_id, url, name, category_id, language, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, url, name, category_id, language, is_active, created_at, updated_at
                """
                now = datetime.utcnow()
                await cur.execute(query, (user_id, url, name, category_id, language, True, now, now))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.info(f"[DB] Error creating user RSS feed: {e}")
                return None


async def get_user_rss_feeds(pool, user_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
    """Gets user RSS feeds list"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT id, user_id, url, name, category_id, language, is_active, created_at, updated_at
                FROM user_rss_feeds
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """
                await cur.execute(query, (user_id, limit, offset))
                results = []
                async for row in cur:
                    columns = [desc[0] for desc in cur.description]
                    results.append(dict(zip(columns, row)))
                return results
            except Exception as e:
                logger.info(f"[DB] Error getting user RSS feeds: {e}")
                return []


async def get_user_rss_feed_by_id(pool, user_id: int, feed_id: str) -> Optional[Dict[str, Any]]:
    """Gets specific user RSS feed"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT id, user_id, url, name, category_id, language, is_active, created_at, updated_at
                FROM user_rss_feeds
                WHERE user_id = %s AND id = %s
                """
                await cur.execute(query, (user_id, feed_id))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.info(f"[DB] Error getting user RSS feed by ID: {e}")
                return None


async def update_user_rss_feed(
    pool, user_id: int, feed_id: str, update_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Updates user RSS feed"""
    if not update_data:
        return await get_user_rss_feed_by_id(pool, user_id, feed_id)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                set_parts = []
                params = []
                for key, value in update_data.items():
                    set_parts.append(f"{key} = %s")
                    params.append(value)
                params.append(user_id)
                params.append(feed_id)

                query = f"""
                UPDATE user_rss_feeds
                SET {', '.join(set_parts)}, updated_at = %s
                WHERE user_id = %s AND id = %s
                RETURNING id, user_id, url, name, category_id, language, is_active, created_at, updated_at
                """
                params.append(datetime.utcnow())  # updated_at
                await cur.execute(query, params)
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.info(f"[DB] Error updating user RSS feed: {e}")
                return None


async def delete_user_rss_feed(pool, user_id: int, feed_id: str) -> bool:
    """Deletes user RSS feed"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("DELETE FROM user_rss_feeds WHERE user_id = %s AND id = %s", (user_id, feed_id))
                # Check if a row was affected
                if cur.rowcount > 0:
                    return True
                return False
            except Exception as e:
                logger.info(f"[DB] Error deleting user RSS feed: {e}")
                return False


# --- Functions for getting RSS items ---


async def get_user_rss_items_list(
    pool, user_id: int, display_language: str, original_language: Optional[str], limit: int, offset: int
) -> Tuple[int, List[Tuple], List[str]]:
    """
    Gets RSS items list for current user based on their subscriptions.
    Returns tuple (total_count, results_rows, column_names).
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 1. Get IDs of categories the user is subscribed to
                user_categories = await get_user_categories(pool, user_id)
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
                WHERE nd.rss_feed_id = ANY(%s) -- Фильтр по пользовательским RSS-лентам
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
                nd.source_url as source_url, -- Получаем URL оригинальной новости из published_news_data
                nd.created_at as published_at, -- Используем created_at из published_news_data как published_at
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
                query_params.extend(["ru", "en", "de", "fr", display_language, user_rss_feed_ids])

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
                logger.info(f"[DB] Error in get_user_rss_items_list: {e}")
                raise  # Перебрасываем исключение, чтобы обработать его в API


async def get_user_rss_items_list_by_feed(
    pool, user_id: int, feed_id: str, display_language: str, original_language: Optional[str], limit: int, offset: int
) -> Tuple[int, List[Tuple], List[str]]:
    """
    Gets RSS items list from specific user RSS feed for current user.
    Returns tuple (total_count, results_rows, column_names).
    """
    async with pool.acquire() as conn:
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
                WHERE nd.rss_feed_id = %s -- Фильтр по конкретной пользовательской RSS-ленте
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
                WHERE nd.rss_feed_id = %s -- Filter by specific user RSS feed
                """

                # Add parameters for language JOINs
                query_params.extend(["ru", "en", "de", "fr", display_language, feed_id])

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
                logger.info(f"[DB] Error in get_user_rss_items_list_by_feed: {e}")
                raise  # Re-raise exception to handle it in API


# --- Moved: get_rss_item_by_id function ---
async def get_rss_item_by_id(pool, news_id: str) -> Optional[Tuple]:
    """Gets RSS item by its ID."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Similarly, add JOIN with rss_feeds, categories, sources and translations
                # Fix parameters and remove references to non-existent pn table
                query = """
                SELECT
                nd.*,
                COALESCE(c.name, 'Unknown Category') AS category_name,
                COALESCE(s.name, 'Unknown Source') AS source_name,
                nd.source_url as source_url, -- Получаем URL оригинальной новости из published_news_data
                nd.created_at as published_at, -- Используем created_at из published_news_data как published_at
                nt_ru.translated_title as title_ru,
                nt_ru.translated_content as content_ru,
                nt_en.translated_title as title_en,
                nt_en.translated_content as content_en,
                nt_de.translated_title as title_de,
                nt_de.translated_content as content_de,
                nt_fr.translated_title as title_fr,
                nt_fr.translated_content as content_fr
                FROM published_news_data nd
                LEFT JOIN rss_feeds rf ON nd.rss_feed_id = rf.id
                LEFT JOIN categories c ON nd.category_id = c.id
                LEFT JOIN sources s ON rf.source_id = s.id
                LEFT JOIN news_translations nt_ru ON nd.news_id = nt_ru.news_id AND nt_ru.language = %s
                LEFT JOIN news_translations nt_en ON nd.news_id = nt_en.news_id AND nt_en.language = %s
                LEFT JOIN news_translations nt_de ON nd.news_id = nt_de.news_id AND nt_de.language = %s
                LEFT JOIN news_translations nt_fr ON nd.news_id = nt_fr.news_id AND nt_fr.language = %s
                WHERE nd.news_id = %s
                """
                # Fix query parameters
                query_params = ["ru", "en", "de", "fr", news_id]
                await cur.execute(query, query_params)
                result = await cur.fetchone()
                return result
            except Exception as e:
                logger.info(f"[DB] Error getting RSS item by ID: {e}")
                raise


# --- Added: wrapper for get_rss_item_by_id, returning row and columns ---
async def get_rss_item_by_id_full(pool, news_id: str) -> Tuple[Optional[Tuple], List[str]]:
    """Gets RSS item by its ID, returning tuple (row, columns)."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT
                nd.*,
                COALESCE(c.name, 'Unknown Category') AS category_name,
                COALESCE(s.name, 'Unknown Source') AS source_name,
                COALESCE(s.alias, 'unknown') AS source_alias,
                nd.source_url as source_url,
                nd.created_at as published_at,
                nt_ru.translated_title as title_ru,
                nt_ru.translated_content as content_ru,
                nt_en.translated_title as title_en,
                nt_en.translated_content as content_en,
                nt_de.translated_title as title_de,
                nt_de.translated_content as content_de,
                nt_fr.translated_title as title_fr,
                nt_fr.translated_content as content_fr
                FROM published_news_data nd
                LEFT JOIN rss_feeds rf ON nd.rss_feed_id = rf.id
                LEFT JOIN categories c ON nd.category_id = c.id
                LEFT JOIN sources s ON rf.source_id = s.id
                LEFT JOIN news_translations nt_ru ON nd.news_id = nt_ru.news_id AND nt_ru.language = %s
                LEFT JOIN news_translations nt_en ON nd.news_id = nt_en.news_id AND nt_en.language = %s
                LEFT JOIN news_translations nt_de ON nd.news_id = nt_de.news_id AND nt_de.language = %s
                LEFT JOIN news_translations nt_fr ON nd.news_id = nt_fr.news_id AND nt_fr.language = %s
                WHERE nd.news_id = %s
                """
                query_params = ["ru", "en", "de", "fr", news_id]
                await cur.execute(query, query_params)
                result = await cur.fetchone()
                columns = [desc[0] for desc in cur.description]
                return result, columns
            except Exception as e:
                logger.info(f"[DB] Error getting RSS item by ID (full): {e}")
                return None, []


async def get_all_rss_items_list(
    pool,
    original_language: Optional[str],
    category_id: Optional[List[int]],
    source_id: Optional[List[int]],
    telegram_published: Optional[bool],
    from_date: Optional[datetime],
    search_phrase: Optional[str],
    before_published_at: Optional[datetime],
    cursor_news_id: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[int, List[Tuple], List[str]]:
    """
    Gets list of all RSS items with filtering.
    Always joins translations for all languages (ru/en/de/fr).
    Supports keyset pagination via before_published_at and cursor_news_id.
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                params = []
                # Basic SELECT
                select_parts = [
                    "nd.*",
                    "COALESCE(c.name, 'Unknown Category') AS category_name",
                    "COALESCE(s.name, 'Unknown Source') AS source_name",
                    "COALESCE(s.alias, 'unknown') AS source_alias",
                    "nd.source_url as source_url",
                    "nd.created_at as published_at",
                    "nt_ru.translated_title as title_ru",
                    "nt_ru.translated_content as content_ru",
                    "nt_en.translated_title as title_en",
                    "nt_en.translated_content as content_en",
                    "nt_de.translated_title as title_de",
                    "nt_de.translated_content as content_de",
                    "nt_fr.translated_title as title_fr",
                    "nt_fr.translated_content as content_fr",
                ]
                join_parts = [
                    "LEFT JOIN rss_feeds rf ON nd.rss_feed_id = rf.id",
                    "LEFT JOIN categories c ON nd.category_id = c.id",
                    "LEFT JOIN sources s ON rf.source_id = s.id",
                    "LEFT JOIN news_translations nt_ru ON nd.news_id = nt_ru.news_id AND nt_ru.language = 'ru'",
                    "LEFT JOIN news_translations nt_en ON nd.news_id = nt_en.news_id AND nt_en.language = 'en'",
                    "LEFT JOIN news_translations nt_de ON nd.news_id = nt_de.news_id AND nt_de.language = 'de'",
                    "LEFT JOIN news_translations nt_fr ON nd.news_id = nt_fr.news_id AND nt_fr.language = 'fr'",
                ]

                # Add publication JOINs if telegram_published filter is used
                telegram_published_value = None
                if telegram_published is not None:
                    telegram_published_value = (
                        bool(str(telegram_published).lower() == "true")
                        if isinstance(telegram_published, str)
                        else bool(telegram_published)
                    )
                    join_parts.extend([
                        "LEFT JOIN (SELECT DISTINCT news_id FROM rss_items_telegram_published rtp JOIN news_translations nt ON rtp.translation_id = nt.id) pub_trans ON nd.news_id = pub_trans.news_id",
                        "LEFT JOIN (SELECT DISTINCT news_id FROM rss_items_telegram_published_originals) pub_orig ON nd.news_id = pub_orig.news_id"
                    ])

                query = f"""
                SELECT {', '.join(select_parts)}
                FROM published_news_data nd
                {chr(10).join(join_parts)}
                WHERE 1=1
                """

                # Filters
                if original_language:
                    query += " AND nd.original_language = %s"
                    params.append(original_language)
                if category_id:
                    if len(category_id) == 1:
                        query += " AND nd.category_id = %s"
                        params.append(category_id[0])
                    else:
                        placeholders = ",".join(["%s"] * len(category_id))
                        query += f" AND nd.category_id IN ({placeholders})"
                        params.extend(category_id)
                if source_id:
                    if len(source_id) == 1:
                        query += " AND rf.source_id = %s"
                        params.append(source_id[0])
                    else:
                        placeholders = ",".join(["%s"] * len(source_id))
                        query += f" AND rf.source_id IN ({placeholders})"
                        params.extend(source_id)

                if telegram_published is not None:
                    if telegram_published_value:
                        # For published: check either translations or originals
                        query += " AND (pub_trans.news_id IS NOT NULL OR pub_orig.news_id IS NOT NULL)"
                    else:
                        # For unpublished: check absence of both translations and originals
                        query += " AND pub_trans.news_id IS NULL AND pub_orig.news_id IS NULL"

                if from_date is not None:
                    query += " AND nd.created_at > %s"
                    params.append(from_date)

                # Search: OR conditions for each field, without concatenations
                phrase = None
                if search_phrase:
                    sp = search_phrase.strip()
                    if sp:
                        phrase = f"%{sp}%"
                        query += " AND ((nd.original_title ILIKE %s OR nd.original_content ILIKE %s))"
                        params.extend([phrase, phrase])

                # Keyset pagination (by descending created_at, then news_id)
                if before_published_at is not None:
                    query += " AND (nd.created_at < %s OR (nd.created_at = %s AND nd.news_id < %s))"
                    params.extend([before_published_at, before_published_at, cursor_news_id or "\uffff"])

                query += " ORDER BY nd.created_at DESC, nd.news_id DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                await cur.execute(query, params)
                results = [row async for row in cur]
                columns = [desc[0] for desc in cur.description]

                # Count total number (without keyset cursor, but with other filters)
                count_query = """
                SELECT COUNT(*)
                FROM published_news_data nd
                LEFT JOIN rss_feeds rf ON nd.rss_feed_id = rf.id
                """
                count_params = []

                # Add publication JOINs if telegram_published filter is used
                if telegram_published is not None:
                    count_query += """
                LEFT JOIN (SELECT DISTINCT news_id FROM rss_items_telegram_published rtp JOIN news_translations nt ON rtp.translation_id = nt.id) pub_trans ON nd.news_id = pub_trans.news_id
                LEFT JOIN (SELECT DISTINCT news_id FROM rss_items_telegram_published_originals) pub_orig ON nd.news_id = pub_orig.news_id
                    """

                count_query += "WHERE 1=1"

                if original_language:
                    count_query += " AND nd.original_language = %s"
                    count_params.append(original_language)
                if category_id:
                    if len(category_id) == 1:
                        count_query += " AND nd.category_id = %s"
                        count_params.append(category_id[0])
                    else:
                        placeholders = ",".join(["%s"] * len(category_id))
                        count_query += f" AND nd.category_id IN ({placeholders})"
                        count_params.extend(category_id)
                if source_id:
                    if len(source_id) == 1:
                        count_query += " AND rf.source_id = %s"
                        count_params.append(source_id[0])
                    else:
                        placeholders = ",".join(["%s"] * len(source_id))
                        count_query += f" AND rf.source_id IN ({placeholders})"
                        count_params.extend(source_id)
                if telegram_published is not None:
                    if telegram_published_value:
                        # For published: check either translations or originals
                        count_query += " AND (pub_trans.news_id IS NOT NULL OR pub_orig.news_id IS NOT NULL)"
                    else:
                        # For unpublished: check absence of both translations and originals
                        count_query += " AND pub_trans.news_id IS NULL AND pub_orig.news_id IS NULL"
                if from_date is not None:
                    count_query += " AND nd.created_at > %s"
                    count_params.append(from_date)

                if phrase:
                    count_query += " AND (nd.original_title ILIKE %s OR nd.original_content ILIKE %s)"
                    count_params.extend([phrase, phrase])

                await cur.execute(count_query, count_params)
                total_count_row = await cur.fetchone()
                total_count = total_count_row[0] if total_count_row else 0

                return total_count, results, columns
            except Exception as e:
                logger.info(f"[DB] Error executing query in get_all_rss_items_list: {e}")
                raise


async def get_all_categories_list(
    pool, limit: int, offset: int, source_ids: Optional[List[int]] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Gets list of all categories with pagination and filtering by source_id.
    Returns tuple (total_count, results).
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Basic query
                count_query = "SELECT COUNT(*) FROM categories WHERE id != %s"
                data_query = "SELECT id, name FROM categories WHERE id != %s"
                conditions = []
                params = [config.USER_DEFINED_RSS_CATEGORY_ID]
                count_params = [config.USER_DEFINED_RSS_CATEGORY_ID]

                # Add filter by source_id if provided
                if source_ids:
                    placeholders = ",".join(["%s"] * len(source_ids))
                    conditions.append(
                        f"id IN (SELECT category_id FROM source_categories WHERE source_id IN ({placeholders}) AND category_id != %s)"
                    )
                    params.extend(source_ids)
                    params.append(config.USER_DEFINED_RSS_CATEGORY_ID)
                    count_params.extend(source_ids)
                    count_params.append(config.USER_DEFINED_RSS_CATEGORY_ID)

                where_clause = ""
                if conditions:
                    where_clause = " AND " + " AND ".join(conditions)
                else:
                    where_clause = ""

                # Get total count
                await cur.execute(count_query + where_clause, count_params)
                total_count_row = await cur.fetchone()
                total_count = total_count_row[0] if total_count_row else 0

                # Get list with pagination
                final_query = data_query + where_clause + " ORDER BY name LIMIT %s OFFSET %s"
                await cur.execute(final_query, params + [limit, offset])
                results = []
                async for row in cur:
                    results.append({"id": row[0], "name": row[1]})

                return total_count, results
            except Exception as e:
                logger.info(f"[DB] Error executing query in get_all_categories_list: {e}")
                raise


async def activate_user_and_use_verification_code(pool, user_id: int, verification_code: str) -> bool:
    """In one transaction activates user and marks verification code as used.
    Returns True on success, False on error or if code not found/invalid.
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("BEGIN")
                await cur.execute(
                    """
                    SELECT id FROM user_verification_codes
                    WHERE user_id = %s AND verification_code = %s AND used_at IS NULL AND expires_at > NOW()
                    FOR UPDATE
                    """,
                    (user_id, verification_code),
                )
                rec = await cur.fetchone()
                if not rec:
                    await cur.execute("ROLLBACK")
                    return False
                await cur.execute("UPDATE users SET is_active = TRUE, is_verified = TRUE WHERE id = %s", (user_id,))
                await cur.execute("UPDATE user_verification_codes SET used_at = NOW() WHERE id = %s", (rec[0],))
                await cur.execute("COMMIT")
                return True
            except Exception as e:
                await cur.execute("ROLLBACK")
                logger.error(f"[DB] Error activating user with verification code: {e}")
                return False

async def confirm_password_reset_transaction(pool, token: str, new_password_hash: str) -> bool:
    """In one transaction validates reset token, updates password and deletes token."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                now = datetime.now(timezone.utc)
                await cur.execute("BEGIN")
                await cur.execute(
                    """
                    SELECT user_id, expires_at FROM password_reset_tokens
                    WHERE token = %s AND expires_at > %s AND used_at IS NULL
                    FOR UPDATE
                    """,
                    (token, now),
                )
                token_record = await cur.fetchone()
                if not token_record:
                    await cur.execute("ROLLBACK")
                    return False
                user_id, expires_at = token_record
                if expires_at < now:
                    await cur.execute("ROLLBACK")
                    return False
                await cur.execute(
                    "UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s",
                    (new_password_hash, now, user_id),
                )
                await cur.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
                if cur.rowcount == 0:
                    await cur.execute("ROLLBACK")
                    return False
                await cur.execute("COMMIT")
                return True
            except Exception as e:
                await cur.execute("ROLLBACK")
                logger.error(f"[DB] Error confirming password reset: {e}")
                return False

async def get_all_sources_list(
    pool, limit: int, offset: int, category_id: Optional[List[int]] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Gets list of all sources with pagination and optional filtering by categories.
    Returns tuple (total_count, results).
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # Form basic query parts
                base_query_select = """
                    SELECT DISTINCT s.id, s.name, s.description, s.alias, s.logo, s.site_url
                    FROM sources s
                """
                base_query_count = """
                    SELECT COUNT(DISTINCT s.id)
                    FROM sources s
                """

                # If categories provided, add JOIN
                if category_id:
                    join_clause = """
                        JOIN source_categories sc ON s.id = sc.source_id
                        WHERE sc.category_id = ANY(%s)
                    """
                    full_query_select = base_query_select + join_clause + " ORDER BY s.name LIMIT %s OFFSET %s"
                    full_query_count = base_query_count + join_clause
                else:
                    full_query_select = base_query_select + " ORDER BY s.name LIMIT %s OFFSET %s"
                    full_query_count = base_query_count

                # Execute count of total records
                await cur.execute(full_query_count, (category_id,) if category_id else ())
                total_count_row = await cur.fetchone()
                total_count = total_count_row[0] if total_count_row else 0

                # Execute data selection with pagination
                params = (category_id, limit, offset) if category_id else (limit, offset)
                await cur.execute(full_query_select, params)

                results = []
                async for row in cur:
                    results.append(
                        {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "alias": row[3],
                            "logo": row[4],
                            "site_url": row[5],
                        }
                    )

                return total_count, results
            except Exception as e:
                logger.info(f"[DB] Error executing query in get_all_sources_list: {e}")
                raise


async def get_recent_rss_items_for_broadcast(pool, last_check_time: datetime) -> List[Dict[str, Any]]:
    """
    Gets list of recent RSS items for WebSocket broadcast.
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT
                    nd.news_id,
                    nd.original_title,
                    nd.original_language,
                    c.name as category_name,
                    nd.created_at as published_at,
                    nt_ru.translated_title as title_ru,
                    nt_ru.translated_content as content_ru,
                    nt_en.translated_title as title_en,
                    nt_en.translated_content as content_en,
                    nt_de.translated_title as title_de,
                    nt_de.translated_content as content_de,
                    nt_fr.translated_title as title_fr,
                    nt_fr.translated_content as content_fr
                FROM published_news_data nd
                LEFT JOIN rss_feeds rf ON nd.rss_feed_id = rf.id
                LEFT JOIN categories c ON nd.category_id = c.id
                LEFT JOIN sources s ON rf.source_id = s.id
                LEFT JOIN news_translations nt_ru ON nd.news_id = nt_ru.news_id AND nt_ru.language = 'ru'
                LEFT JOIN news_translations nt_en ON nd.news_id = nt_en.news_id AND nt_en.language = 'en'
                LEFT JOIN news_translations nt_de ON nd.news_id = nt_de.news_id AND nt_de.language = 'de'
                LEFT JOIN news_translations nt_fr ON nd.news_id = nt_fr.news_id AND nt_fr.language = 'fr'
                WHERE nd.created_at > %s
                ORDER BY nd.created_at DESC
                LIMIT 10
                """
                check_time_str = last_check_time.strftime("%Y-%m-%d %H:%M:%S")
                await cur.execute(query, (check_time_str,))
                results = []
                async for row in cur:
                    results.append(row)

                # Convert to format for sending
                columns = [desc[0] for desc in cur.description]
                rss_items_payload = []
                for row in results:
                    row_dict = dict(zip(columns, row))
                    rss_items_payload.append(
                        {
                            "news_id": row_dict["news_id"],
                            "original_title": row_dict["original_title"],
                            "original_language": row_dict["original_language"],
                            "category": row_dict["category_name"],
                            "published_at": row_dict["published_at"].isoformat() if row_dict["published_at"] else None,
                            "translations": {
                                "ru": {"title": row_dict.get("title_ru"), "content": row_dict.get("content_ru")},
                                "en": {"title": row_dict.get("title_en"), "content": row_dict.get("content_en")},
                                "de": {"title": row_dict.get("title_de"), "content": row_dict.get("content_de")},
                                "fr": {"title": row_dict.get("title_fr"), "content": row_dict.get("content_fr")},
                            },
                        }
                    )
                return rss_items_payload
            except Exception as e:
                logger.info(f"[DB] Error in get_recent_news_for_broadcast: {e}")
                return []  # Return empty list on error to not interrupt background task


# --- Functions for working with user API keys ---


async def create_user_api_key(pool, user_id: int, plain_key: str, limits: Dict[str, int], expires_at: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Creates new API key for user"""
    import json
    from api.deps import hash_api_key
    key_hash = hash_api_key(plain_key)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                INSERT INTO user_api_keys (user_id, key_hash, limits, is_active, created_at, expires_at)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s)
                RETURNING id, user_id, key_hash, limits, is_active, created_at, expires_at
                """
                now = datetime.utcnow()
                await cur.execute(query, (user_id, key_hash, json.dumps(limits), True, now, expires_at))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, result))
                    data["key"] = plain_key  # Add plain key for response
                    return data
                return None
            except Exception as e:
                logger.error(f"[DB] Error creating user API key: {e}")
                return None


async def get_user_api_keys(pool, user_id: int) -> List[Dict[str, Any]]:
    """Gets user API keys list"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT id, user_id, limits, is_active, created_at, expires_at
                FROM user_api_keys
                WHERE user_id = %s
                ORDER BY created_at DESC
                """
                await cur.execute(query, (user_id,))
                results = []
                async for row in cur:
                    columns = [desc[0] for desc in cur.description]
                    results.append(dict(zip(columns, row)))
                return results
            except Exception as e:
                logger.error(f"[DB] Error getting user API keys: {e}")
                return []


async def get_user_api_key_by_key(pool, plain_key: str) -> Optional[Dict[str, Any]]:
    """Gets API key by key value"""
    from api.deps import hash_api_key
    key_hash = hash_api_key(plain_key)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT id, user_id, limits, is_active, created_at, expires_at
                FROM user_api_keys
                WHERE key_hash = %s AND is_active = TRUE AND (expires_at IS NULL OR expires_at > %s)
                """
                await cur.execute(query, (key_hash, datetime.utcnow()))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.error(f"[DB] Error getting user API key by key: {e}")
                return None


async def update_user_api_key(pool, user_id: int, key_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates user API key"""
    if not update_data:
        return await get_user_api_key_by_id(pool, user_id, key_id)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                set_parts = []
                params = []
                for key, value in update_data.items():
                    set_parts.append(f"{key} = %s")
                    params.append(value)
                params.append(user_id)
                params.append(key_id)

                query = f"""
                UPDATE user_api_keys
                SET {', '.join(set_parts)}
                WHERE user_id = %s AND id = %s
                RETURNING id, user_id, limits, is_active, created_at, expires_at
                """
                await cur.execute(query, params)
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.error(f"[DB] Error updating user API key: {e}")
                return None


async def get_user_api_key_by_id(pool, user_id: int, key_id: int) -> Optional[Dict[str, Any]]:
    """Gets specific user API key by ID"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT id, user_id, limits, is_active, created_at, expires_at
                FROM user_api_keys
                WHERE user_id = %s AND id = %s
                """
                await cur.execute(query, (user_id, key_id))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.error(f"[DB] Error getting user API key by ID: {e}")
                return None


async def delete_user_api_key(pool, user_id: int, key_id: int) -> bool:
    """Deletes user API key"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = "DELETE FROM user_api_keys WHERE user_id = %s AND id = %s"
                await cur.execute(query, (user_id, key_id))
                return cur.rowcount > 0
            except Exception as e:
                logger.error(f"[DB] Error deleting user API key: {e}")
                return False


# --- Functions for working with Telegram linking ---


async def get_telegram_link_status(pool, user_id: int) -> Optional[Dict[str, Any]]:
    """Gets Telegram link status for user"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                query = """
                SELECT telegram_id, linked_at
                FROM user_telegram_links
                WHERE user_id = %s
                """
                await cur.execute(query, (user_id,))
                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None
            except Exception as e:
                logger.error(f"[DB] Error getting Telegram link status: {e}")
                return None
