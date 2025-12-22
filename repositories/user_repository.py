# repositories/user_repository.py - User repository implementation
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from interfaces import IUserRepository
from exceptions import DatabaseException

logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    """PostgreSQL implementation of user repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at FROM users WHERE email = %s",
                        (email,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "email": row[1], "password_hash": row[2],
                            "language": row[3], "is_active": row[4], "is_verified": row[5], "is_deleted": row[6],
                            "created_at": row[7], "updated_at": row[8]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get user by email {email}: {str(e)}")

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at FROM users WHERE id = %s",
                        (user_id,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "email": row[1], "password_hash": row[2],
                            "language": row[3], "is_active": row[4], "is_verified": row[5], "is_deleted": row[6],
                            "created_at": row[7], "updated_at": row[8]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get user by id {user_id}: {str(e)}")

    async def create_user(self, email: str, password_hash: str, language: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "INSERT INTO users (email, password_hash, language) VALUES (%s, %s, %s) RETURNING id, email, language, is_active, is_verified, created_at",
                        (email, password_hash, language)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "email": row[1], "language": row[2],
                            "is_active": row[3], "is_verified": row[4], "created_at": row[5]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to create user {email}: {str(e)}")

    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)

        query = f"UPDATE users SET {', '.join(set_parts)}, updated_at = NOW() WHERE id = %s RETURNING id, email, language, is_active, is_verified, updated_at"
        values.append(user_id)

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0], "email": row[1], "language": row[2],
                            "is_active": row[3], "is_verified": row[4], "updated_at": row[5]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to update user {user_id}: {str(e)}")

    async def delete_user(self, user_id: int) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("UPDATE users SET is_deleted = TRUE, updated_at = NOW() WHERE id = %s", (user_id,))
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to delete user {user_id}: {str(e)}")

    async def save_verification_code(self, user_id: int, code: str, expires_at: datetime) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO email_verifications (user_id, verification_code, expires_at) VALUES (%s, %s, %s)",
                    (user_id, code, expires_at)
                )
                return cur.rowcount > 0

    async def activate_user_and_use_verification_code(self, user_id: int, code: str) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Start transaction
                await cur.execute("BEGIN")

                try:
                    # Check if verification code exists and is valid
                    await cur.execute(
                        "SELECT id FROM email_verifications WHERE user_id = %s AND verification_code = %s AND expires_at > NOW() AND used = FALSE",
                        (user_id, code)
                    )
                    verification_row = await cur.fetchone()

                    if not verification_row:
                        await cur.execute("ROLLBACK")
                        return False

                    # Mark verification code as used
                    await cur.execute(
                        "UPDATE email_verifications SET used = TRUE, used_at = NOW() WHERE id = %s",
                        (verification_row[0],)
                    )

                    # Activate user
                    await cur.execute(
                        "UPDATE users SET is_verified = TRUE, updated_at = NOW() WHERE id = %s",
                        (user_id,)
                    )

                    await cur.execute("COMMIT")
                    return True

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    logger.error(f"Error in activate_user_and_use_verification_code: {e}")
                    return False

    async def save_password_reset_token(self, user_id: int, token: str, expires_at: datetime) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO password_resets (user_id, reset_token, expires_at) VALUES (%s, %s, %s)",
                    (user_id, token, expires_at)
                )
                return cur.rowcount > 0

    async def confirm_password_reset_transaction(self, token: str, new_password_hash: str) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")

                try:
                    # Get user_id from token
                    await cur.execute(
                        "SELECT user_id FROM password_resets WHERE reset_token = %s AND expires_at > NOW() AND used = FALSE",
                        (token,)
                    )
                    reset_row = await cur.fetchone()

                    if not reset_row:
                        await cur.execute("ROLLBACK")
                        return False

                    user_id = reset_row[0]

                    # Update password
                    await cur.execute(
                        "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                        (new_password_hash, user_id)
                    )

                    # Mark token as used
                    await cur.execute(
                        "UPDATE password_resets SET used = TRUE, used_at = NOW() WHERE reset_token = %s",
                        (token,)
                    )

                    await cur.execute("COMMIT")
                    return True

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    logger.error(f"Error in confirm_password_reset_transaction: {e}")
                    return False

    async def delete_password_reset_token(self, token: str) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM password_resets WHERE reset_token = %s", (token,))
                return cur.rowcount > 0

    # Telegram user preferences methods
    async def get_telegram_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get Telegram user settings from user_preferences table"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT subscriptions, language FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                result = await cur.fetchone()

                if result:
                    import json
                    subscriptions = json.loads(result[0]) if result[0] else []
                    return {"subscriptions": subscriptions, "language": result[1]}
                return {"subscriptions": [], "language": "en"}

    async def save_telegram_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save Telegram user settings to user_preferences table"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                import json
                from datetime import datetime

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
                            datetime.now(timezone.utc),
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

                return True

    async def set_telegram_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set Telegram user language"""
        async with self.db_pool.acquire() as conn:
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

    async def get_telegram_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get Telegram subscribers for a specific category"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, subscriptions, language
                    FROM user_preferences
                    """
                )

                subscribers = []
                rows = await cur.fetchall()
                for row in rows:
                    user_id, subscriptions_json, language = row

                    try:
                        import json
                        subscriptions_list = json.loads(subscriptions_json) if subscriptions_json else []

                        if "all" in subscriptions_list or category in subscriptions_list:
                            user = {"id": user_id, "language_code": language if language else "en"}
                            subscribers.append(user)

                    except json.JSONDecodeError:
                        continue

                return subscribers

    async def remove_telegram_blocked_user(self, user_id: int) -> bool:
        """Remove blocked Telegram user from database"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                return cur.rowcount > 0

    async def get_all_telegram_users(self) -> List[int]:
        """Get all Telegram users"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM user_preferences")
                users = []
                rows = await cur.fetchall()
                for row in rows:
                    users.append(row[0])
                return users

    # Web user Telegram linking methods
    async def generate_telegram_link_code(self, user_id: int) -> str:
        """Generate code for linking Telegram account"""
        import secrets
        from datetime import datetime

        link_code = secrets.token_urlsafe(16)
        async with self.db_pool.acquire() as conn:
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
                    (user_id, link_code, datetime.now(timezone.utc)),
                )
        return link_code

    async def confirm_telegram_link(self, telegram_id: int, link_code: str) -> bool:
        """Confirm Telegram account linking by code"""
        from datetime import datetime, timedelta

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Find record with code
                await cur.execute(
                    """
                    SELECT user_id FROM user_telegram_links
                    WHERE link_code = %s AND linked_at IS NULL
                    AND created_at > %s
                    """,
                    (link_code, datetime.now(timezone.utc) - timedelta(hours=24)),
                )

                result = await cur.fetchone()
                if not result:
                    return False

                user_id = result[0]

                # Check if this Telegram ID is already linked
                await cur.execute(
                    "SELECT 1 FROM user_telegram_links WHERE telegram_id = %s AND linked_at IS NOT NULL",
                    (telegram_id,)
                )
                if await cur.fetchone():
                    return False  # Already linked

                # Update record
                await cur.execute(
                    """
                    UPDATE user_telegram_links
                    SET telegram_id = %s, linked_at = %s
                    WHERE link_code = %s
                    """,
                    (telegram_id, datetime.now(timezone.utc), link_code),
                )

                return True

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get web user by Telegram ID"""
        async with self.db_pool.acquire() as conn:
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

    async def unlink_telegram(self, user_id: int) -> bool:
        """Unlink Telegram account from web user"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE user_telegram_links SET linked_at = NULL, telegram_id = NULL WHERE user_id = %s",
                    (user_id,)
                )
                return cur.rowcount > 0

    async def get_telegram_link_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get Telegram link status for user"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        """
                        SELECT telegram_id, linked_at
                        FROM user_telegram_links
                        WHERE user_id = %s
                        """,
                        (user_id,)
                    )
                    result = await cur.fetchone()
                    if result:
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, result))
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get Telegram link status for user {user_id}: {str(e)}")

    # Verification codes methods (using user_verification_codes table)
    async def verify_user_email(self, email: str, verification_code: str) -> Optional[int]:
        """Verify verification code and return user_id if valid"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        """
                        SELECT uvc.user_id
                        FROM user_verification_codes uvc
                        JOIN users u ON uvc.user_id = u.id
                        WHERE u.email = %s
                          AND uvc.verification_code = %s
                          AND uvc.used_at IS NULL
                          AND uvc.expires_at > %s
                        """,
                        (email, verification_code, datetime.now(timezone.utc))
                    )
                    result = await cur.fetchone()
                    return result[0] if result else None
                except Exception as e:
                    raise DatabaseException(f"Failed to verify user email {email}: {str(e)}")

    async def get_active_verification_code(self, user_id: int, verification_code: str) -> Optional[dict]:
        """Get active verification code for user"""
        async with self.db_pool.acquire() as conn:
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
                    raise DatabaseException(f"Failed to get active verification code for user {user_id}: {str(e)}")

    async def mark_verification_code_used(self, code_id: int) -> bool:
        """Mark verification code as used"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("UPDATE user_verification_codes SET used_at = NOW() WHERE id = %s", (code_id,))
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to mark verification code {code_id} as used: {str(e)}")

    async def get_password_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get password reset token data if valid"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        """
                        SELECT user_id, expires_at FROM password_reset_tokens
                        WHERE token = %s AND expires_at > %s
                        """,
                        (token, datetime.now(timezone.utc))
                    )
                    result = await cur.fetchone()
                    if result:
                        return {"user_id": result[0], "expires_at": result[1]}
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get password reset token {token}: {str(e)}")

    async def activate_user_and_use_verification_code(self, user_id: int, verification_code: str) -> bool:
        """In one transaction activates user and marks verification code as used"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")
                try:
                    # Check if verification code exists and is valid
                    await cur.execute(
                        "SELECT id FROM user_verification_codes WHERE user_id = %s AND verification_code = %s AND used_at IS NULL AND expires_at > NOW() FOR UPDATE",
                        (user_id, verification_code)
                    )
                    verification_row = await cur.fetchone()

                    if not verification_row:
                        await cur.execute("ROLLBACK")
                        return False

                    # Mark verification code as used
                    await cur.execute(
                        "UPDATE user_verification_codes SET used_at = NOW() WHERE id = %s",
                        (verification_row[0],)
                    )

                    # Activate user
                    await cur.execute(
                        "UPDATE users SET is_active = TRUE, is_verified = TRUE WHERE id = %s",
                        (user_id,)
                    )

                    await cur.execute("COMMIT")
                    return True

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise DatabaseException(f"Failed to activate user and use verification code: {str(e)}")