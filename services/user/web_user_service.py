# services/user/web_user_service.py
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from utils.database import DatabaseMixin, db_operation
from interfaces import IWebUserService

logger = logging.getLogger(__name__)


class WebUserService(DatabaseMixin, IWebUserService):
    """Service for managing web users and Telegram linking"""

    def __init__(self):
        pass

    @db_operation
    async def generate_telegram_link_code(self, pool, user_id: int) -> str:
        """Generate code for linking Telegram account"""
        import secrets

        link_code = secrets.token_urlsafe(16)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Delete old codes for this user
                await cur.execute(
                    "DELETE FROM user_telegram_links WHERE user_id = %s AND linked_at IS NULL",
                    (user_id,)
                )
                # Create new code
                await cur.execute(
                    """
                    INSERT INTO user_telegram_links (user_id, link_code, created_at)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, link_code, datetime.utcnow()),
                )
                logger.info(f"[WebUserService] Generated link code for user {user_id}")
                return link_code

    @db_operation
    async def confirm_telegram_link(self, pool, telegram_id: int, link_code: str) -> bool:
        """Confirm Telegram account linking by code"""
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
                    logger.warning(f"[WebUserService] Invalid or expired link code: {link_code}")
                    return False

                user_id = result[0]

                # Check if this Telegram ID is already linked
                await cur.execute(
                    "SELECT 1 FROM user_telegram_links WHERE telegram_id = %s AND linked_at IS NOT NULL",
                    (telegram_id,)
                )
                if await cur.fetchone():
                    logger.warning(f"[WebUserService] Telegram ID {telegram_id} already linked")
                    return False  # Already linked

                # Update record
                await cur.execute(
                    """
                    UPDATE user_telegram_links
                    SET telegram_id = %s, linked_at = %s
                    WHERE link_code = %s
                    """,
                    (telegram_id, datetime.utcnow(), link_code),
                )

                logger.info(f"[WebUserService] Linked Telegram ID {telegram_id} to user {user_id}")
                return True

    @db_operation
    async def get_user_by_telegram_id(self, pool, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get web user by Telegram ID"""
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
                    user_data = dict(zip(columns, result))
                    logger.debug(f"[WebUserService] Found user {user_data['id']} for Telegram ID {telegram_id}")
                    return user_data
                logger.debug(f"[WebUserService] No user found for Telegram ID {telegram_id}")
                return None

    @db_operation
    async def unlink_telegram(self, pool, user_id: int) -> bool:
        """Unlink Telegram account from web user"""
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE user_telegram_links SET linked_at = NULL, telegram_id = NULL WHERE user_id = %s",
                    (user_id,)
                )
                success = cur.rowcount > 0
                if success:
                    logger.info(f"[WebUserService] Unlinked Telegram for user {user_id}")
                else:
                    logger.warning(f"[WebUserService] No Telegram link found for user {user_id}")
                return success