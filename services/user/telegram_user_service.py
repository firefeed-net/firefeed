# services/user/telegram_user_service.py
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from utils.database import DatabaseMixin, db_operation
from interfaces import ITelegramUserService

logger = logging.getLogger(__name__)


class TelegramUserService(DatabaseMixin, ITelegramUserService):
    """Service for managing Telegram bot users and their preferences"""

    def __init__(self):
        pass

    @db_operation
    async def _get_user_settings(self, pool, user_id: int) -> Dict[str, Any]:
        """Get user settings from database"""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT subscriptions, language FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                result = await cur.fetchone()

                if result:
                    subscriptions = json.loads(result[0]) if result[0] else []
                    logger.debug(
                        f"[DB] [TelegramUserService] Got settings for user {user_id}: subscriptions={subscriptions}, language={result[1]}"
                    )
                    return {"subscriptions": subscriptions, "language": result[1]}
                logger.debug(
                    f"[DB] [TelegramUserService] Settings for user {user_id} not found, returning defaults"
                )
                return {"subscriptions": [], "language": "en"}

    @db_operation
    async def _save_user_settings(self, pool, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save user settings to database"""
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

                logger.debug(
                    f"[DB] [TelegramUserService] Saved settings for user {user_id}: subscriptions={subscriptions}, language={language}"
                )
                return True

    @db_operation
    async def _set_user_language(self, pool, user_id: int, lang_code: str) -> bool:
        """Set user language"""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Check if record exists
                await cur.execute(
                    "SELECT id FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                exists = await cur.fetchone()

                if exists:
                    # Update existing record
                    await cur.execute(
                        "UPDATE user_preferences SET language = %s WHERE user_id = %s",
                        (lang_code, user_id)
                    )
                else:
                    # Insert new record
                    await cur.execute(
                        "INSERT INTO user_preferences (user_id, language) VALUES (%s, %s)",
                        (user_id, lang_code)
                    )
                return True

    @db_operation
    async def _get_subscribers_for_category(self, pool, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for a specific category"""
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
                        logger.warning(f"[DB] [TelegramUserService] Invalid JSON for user {user_id}: {subscriptions_json}")
                        continue

                return subscribers

    @db_operation
    async def _get_all_users(self, pool) -> List[int]:
        """Get list of all users"""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM user_preferences")
                user_ids = []
                async for row in cur:
                    user_ids.append(row[0])
                return user_ids

    # Public methods
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        return await self._get_user_settings(user_id)

    async def save_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save user settings"""
        return await self._save_user_settings(user_id, subscriptions, language)

    async def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set user language"""
        return await self._set_user_language(user_id, lang_code)

    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Get user subscriptions only"""
        settings = await self.get_user_settings(user_id)
        return settings["subscriptions"]

    async def get_user_language(self, user_id: int) -> str:
        """Get user language only"""
        settings = await self.get_user_settings(user_id)
        return settings["language"]

    async def get_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for category"""
        return await self._get_subscribers_for_category(category)

    async def get_all_users(self) -> List[int]:
        """Get all users"""
        return await self._get_all_users()