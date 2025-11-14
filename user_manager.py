import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from utils.database import DatabaseMixin, db_operation

logger = logging.getLogger(__name__)


class UserManager(DatabaseMixin):
    def __init__(self):
        pass

    # --- Asynchronous methods for working with DB ---

    @db_operation
    async def _get_user_settings(self, pool, user_id):
        """Асинхронный метод: Возвращает все настройки пользователя."""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT subscriptions, language FROM user_preferences WHERE user_id = %s", (user_id,))
                result = await cur.fetchone()

                if result:
                    subscriptions = json.loads(result[0]) if result[0] else []
                    logger.debug(
                        f"[DB] [UserManager] Получены настройки для пользователя {user_id}: subscriptions={subscriptions}, language={result[1]}"
                    )
                    return {"subscriptions": subscriptions, "language": result[1]}
                logger.debug(
                    f"[DB] [UserManager] Настройки для пользователя {user_id} не найдены, возвращаем по умолчанию"
                )
                return {"subscriptions": [], "language": "en"}

    @db_operation
    async def _save_user_settings(self, pool, user_id, subscriptions, language):
        """Асинхронный метод: Сохраняет все настройки пользователя."""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # First try to update existing record
                await cur.execute(
                    """
                    UPDATE user_preferences
                    SET subscriptions = %s, language = %s
                    WHERE user_id = %s
                """,
                    (json.dumps(subscriptions), language, user_id),
                )

                # If no rows were updated, insert new record
                if cur.rowcount == 0:
                    # First ensure user exists in users table
                    await cur.execute(
                        """
                        INSERT INTO users (id, email, password_hash, language, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
                        (
                            user_id,
                            f"user{user_id}@telegram.bot",
                            "dummy_hash",
                            language,
                            True,
                            datetime.utcnow(),
                            datetime.utcnow(),
                        ),
                    )

                    # Now insert preferences
                    await cur.execute(
                        """
                        INSERT INTO user_preferences (user_id, subscriptions, language)
                        VALUES (%s, %s, %s)
                    """,
                        (user_id, json.dumps(subscriptions), language),
                    )

                # In aiopg, transactions are managed automatically, commit not needed
                logger.debug(
                    f"[DB] [UserManager] Сохранены настройки для пользователя {user_id}: subscriptions={subscriptions}, language={language}"
                )
                return True

    @db_operation
    async def _set_user_language(self, pool, user_id, lang_code):
        """Асинхронный метод: Устанавливает язык пользователя."""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO user_preferences (user_id, language)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET language = EXCLUDED.language
                """,
                    (user_id, lang_code),
                )

                return True

    @db_operation
    async def _get_subscribers_for_category(self, pool, category):
        """Асинхронный метод: Получает подписчиков для определенной категории."""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, subscriptions, language
                    FROM user_preferences
                """
                )

                subscribers = []
                async for row in cur:
                    user_id, subscriptions_json, language = row

                    try:
                        subscriptions_list = json.loads(subscriptions_json) if subscriptions_json else []

                        if "all" in subscriptions_list or category in subscriptions_list:
                            user = {"id": user_id, "language_code": language if language else "en"}
                            subscribers.append(user)

                    except json.JSONDecodeError:
                        logger.warning(f"[DB] [UserManager] Invalid JSON for user {user_id}: {subscriptions_json}")
                        continue

                return subscribers

    @db_operation
    async def _get_all_users(self, pool):
        """Асинхронный метод: Получаем список всех пользователей."""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM user_preferences")
                user_ids = []
                async for row in cur:
                    user_ids.append(row[0])
                return user_ids

    # --- Public asynchronous methods ---

    async def get_user_settings(self, user_id):
        """Асинхронно возвращает все настройки пользователя"""
        return await self._get_user_settings(user_id)

    async def save_user_settings(self, user_id, subscriptions, language):
        """Асинхронно сохраняет все настройки пользователя"""
        return await self._save_user_settings(user_id, subscriptions, language)

    async def set_user_language(self, user_id, lang_code):
        """Асинхронно устанавливает язык пользователя"""
        return await self._set_user_language(user_id, lang_code)

    async def get_user_subscriptions(self, user_id):
        """Асинхронно возвращает только подписки пользователя"""
        settings = await self.get_user_settings(user_id)
        subscriptions = settings["subscriptions"]
        # If subscriptions is a list of strings, return as is
        # If list of objects, return them
        return subscriptions

    async def get_user_language(self, user_id):
        """Асинхронно возвращает только язык пользователя"""
        settings = await self.get_user_settings(user_id)
        return settings["language"]

    async def get_subscribers_for_category(self, category):
        """Асинхронно получает подписчиков для определенной категории"""
        return await self._get_subscribers_for_category(category)

    async def get_all_users(self):
        """Асинхронно получаем список всех пользователей"""
        return await self._get_all_users()

    # --- Methods for working with Telegram linking ---

    @db_operation
    async def generate_telegram_link_code(self, pool, user_id: int) -> str:
        """Генерирует код для привязки Telegram аккаунта"""
        import secrets

        link_code = secrets.token_urlsafe(16)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Delete old codes for this user
                await cur.execute(
                    "DELETE FROM user_telegram_links WHERE user_id = %s AND linked_at IS NULL", (user_id,)
                )
                # Create new code
                await cur.execute(
                    """
                    INSERT INTO user_telegram_links (user_id, link_code, created_at)
                    VALUES (%s, %s, %s)
                """,
                    (user_id, link_code, datetime.utcnow()),
                )
                return link_code

    @db_operation
    async def confirm_telegram_link(self, pool, telegram_id: int, link_code: str) -> bool:
        """Подтверждает привязку Telegram аккаунта по коду"""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Find record with code
                await cur.execute(
                    """
                    SELECT user_id FROM user_telegram_links
                    WHERE link_code = %s AND linked_at IS NULL
                    AND created_at > %s
                """,
                    (link_code, datetime.utcnow() - timedelta(hours=24)),
                )

                result = await cur.fetchone()
                if not result:
                    return False

                user_id = result[0]

                # Check if this Telegram ID is already linked
                await cur.execute(
                    "SELECT 1 FROM user_telegram_links WHERE telegram_id = %s AND linked_at IS NOT NULL", (telegram_id,)
                )
                if await cur.fetchone():
                    return False  # Уже привязан

                # Update record
                await cur.execute(
                    """
                    UPDATE user_telegram_links
                    SET telegram_id = %s, linked_at = %s
                    WHERE link_code = %s
                """,
                    (telegram_id, datetime.utcnow(), link_code),
                )

                return True

    @db_operation
    async def get_user_by_telegram_id(self, pool, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по Telegram ID"""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT u.* FROM users u
                    JOIN user_telegram_links utl ON u.id = utl.user_id
                    WHERE utl.telegram_id = %s AND utl.linked_at IS NOT NULL
                """,
                    (telegram_id,),
                )

                result = await cur.fetchone()
                if result:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, result))
                return None

    @db_operation
    async def unlink_telegram(self, pool, user_id: int) -> bool:
        """Отвязывает Telegram аккаунт от пользователя"""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE user_telegram_links SET linked_at = NULL, telegram_id = NULL WHERE user_id = %s", (user_id,)
                )
                return cur.rowcount > 0
