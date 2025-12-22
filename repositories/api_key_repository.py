# repositories/api_key_repository.py - API key repository implementation
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from interfaces import IApiKeyRepository
from exceptions import DatabaseException

logger = logging.getLogger(__name__)


class ApiKeyRepository(IApiKeyRepository):
    """PostgreSQL implementation of API key repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def create_user_api_key(self, user_id: int, key: str, limits: Dict[str, Any], expires_at: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "INSERT INTO user_api_keys (user_id, key_hash, limits, expires_at) VALUES (%s, %s, %s, %s) RETURNING id, user_id, limits, is_active, created_at, expires_at",
                        (user_id, key, limits, expires_at)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "user_id": row[1], "limits": row[2],
                            "is_active": row[3], "created_at": row[4], "expires_at": row[5]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to create user API key for user {user_id}: {str(e)}")

    async def get_user_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, key_hash, limits, is_active, created_at, expires_at FROM user_api_keys WHERE user_id = %s ORDER BY created_at DESC",
                        (user_id,)
                    )

                    keys = []
                    rows = await cur.fetchall()
                    for row in rows:
                        keys.append({
                            "id": row[0], "key": row[1], "limits": row[2],
                            "is_active": row[3], "created_at": row[4], "expires_at": row[5]
                        })

                    return keys
                except Exception as e:
                    raise DatabaseException(f"Failed to get user API keys for user {user_id}: {str(e)}")

    async def get_user_api_key_by_id(self, user_id: int, key_id: int) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, user_id, limits, is_active, created_at, expires_at FROM user_api_keys WHERE user_id = %s AND id = %s",
                        (user_id, key_id)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "user_id": row[1], "limits": row[2],
                            "is_active": row[3], "created_at": row[4], "expires_at": row[5]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get user API key by ID {key_id} for user {user_id}: {str(e)}")

    async def update_user_api_key(self, user_id: int, key_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)

        query = f"UPDATE user_api_keys SET {', '.join(set_parts)}, updated_at = NOW() WHERE user_id = %s AND id = %s RETURNING id, user_id, limits, is_active, updated_at, expires_at"
        values.extend([user_id, key_id])

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "user_id": row[1], "limits": row[2],
                            "is_active": row[3], "updated_at": row[4], "expires_at": row[5]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to update user API key {key_id} for user {user_id}: {str(e)}")

    async def delete_user_api_key(self, user_id: int, key_id: int) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("DELETE FROM user_api_keys WHERE user_id = %s AND id = %s", (user_id, key_id))
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to delete user API key {key_id} for user {user_id}: {str(e)}")

    async def get_user_api_key_by_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, user_id, limits, is_active, created_at, expires_at FROM user_api_keys WHERE key_hash = %s AND is_active = TRUE AND (expires_at IS NULL OR expires_at > %s)",
                        (api_key, datetime.now(timezone.utc))
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "user_id": row[1], "limits": row[2],
                            "is_active": row[3], "created_at": row[4], "expires_at": row[5]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get user API key by key: {str(e)}")