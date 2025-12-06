# repositories/api_key_repository.py - API key repository implementation
import logging
from typing import List, Dict, Any, Optional
from interfaces import IApiKeyRepository

logger = logging.getLogger(__name__)


class ApiKeyRepository(IApiKeyRepository):
    """PostgreSQL implementation of API key repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def create_user_api_key(self, user_id: int, key: str, limits: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO user_api_keys (user_id, key, limits) VALUES (%s, %s, %s) RETURNING id, key, limits, is_active, created_at",
                    (user_id, key, limits)
                )
                row = await cur.fetchone()
                if row:
                    return {
                        "id": row[0], "key": row[1], "limits": row[2],
                        "is_active": row[3], "created_at": row[4]
                    }
        return None

    async def get_user_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, key, limits, is_active, created_at FROM user_api_keys WHERE user_id = %s ORDER BY created_at DESC",
                    (user_id,)
                )

                keys = []
                async for row in cur:
                    keys.append({
                        "id": row[0], "key": row[1], "limits": row[2],
                        "is_active": row[3], "created_at": row[4]
                    })

                return keys

    async def get_user_api_key_by_id(self, user_id: int, key_id: int) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, key, limits, is_active, created_at FROM user_api_keys WHERE user_id = %s AND id = %s",
                    (user_id, key_id)
                )
                row = await cur.fetchone()
                if row:
                    return {
                        "id": row[0], "key": row[1], "limits": row[2],
                        "is_active": row[3], "created_at": row[4]
                    }
        return None

    async def update_user_api_key(self, user_id: int, key_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)

        query = f"UPDATE user_api_keys SET {', '.join(set_parts)}, updated_at = NOW() WHERE user_id = %s AND id = %s RETURNING id, key, limits, is_active, updated_at"
        values.extend([user_id, key_id])

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, values)
                row = await cur.fetchone()
                if row:
                    return {
                        "id": row[0], "key": row[1], "limits": row[2],
                        "is_active": row[3], "updated_at": row[4]
                    }
        return None

    async def delete_user_api_key(self, user_id: int, key_id: int) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM user_api_keys WHERE user_id = %s AND id = %s", (user_id, key_id))
                return cur.rowcount > 0

    async def get_user_api_key_by_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT u.id as user_id, u.email, u.language, u.is_verified, u.is_deleted, k.limits FROM user_api_keys k JOIN users u ON k.user_id = u.id WHERE k.key = %s AND k.is_active = TRUE",
                    (api_key,)
                )
                row = await cur.fetchone()
                if row:
                    return {
                        "user_id": row[0], "email": row[1], "language": row[2],
                        "is_verified": row[3], "is_deleted": row[4], "limits": row[5]
                    }
        return None