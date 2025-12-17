#!/usr/bin/env python3
"""
Module for periodic database cleanup.

Includes functions for deleting unverified and deleted users.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from di_container import get_service
from interfaces import IUserRepository

logger = logging.getLogger(__name__)


async def cleanup_users():
    """Deletes unverified and deleted users."""
    user_repo = get_service(IUserRepository)

    try:
        # Since Repository doesn't have direct SQL access, we'll need to add cleanup methods
        # For now, we'll implement cleanup logic directly using the repository's db_pool
        pool = user_repo.db_pool

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Delete users with is_deleted = TRUE
                await cur.execute("DELETE FROM users WHERE is_deleted = TRUE")
                deleted_count = cur.rowcount
                logger.info(f"Deleted {deleted_count} deleted users")

                # Delete unverified users registered more than 24 hours ago
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                await cur.execute(
                    "DELETE FROM users WHERE is_verified = FALSE AND created_at < %s",
                    (cutoff_time,)
                )
                unverified_count = cur.rowcount
                logger.info(f"Deleted {unverified_count} unverified users (older than 24 hours)")

                total_deleted = deleted_count + unverified_count
                logger.info(f"Total users deleted: {total_deleted}")

    except Exception as e:
        logger.error(f"Error cleaning users: {e}")


async def periodic_cleanup_users():
    """Periodic user cleanup task (every 24 hours)."""
    while True:
        await asyncio.sleep(24 * 60 * 60)  # 24 hours
        try:
            await cleanup_users()
        except Exception as e:
            logger.error(f"Error in periodic user cleanup: {e}")