import logging
from typing import Any, Callable
from functools import wraps
from config import get_shared_db_pool

logger = logging.getLogger(__name__)


class DatabaseMixin:
    """Base class for working with database"""

    async def get_pool(self):
        """Gets shared connection pool from config.py"""
        return await get_shared_db_pool()

    async def close_pool(self):
        """Stub - pool is closed globally"""
        pass


def db_operation(func: Callable) -> Callable:
    """
    Decorator for database operations.
    Automatically gets pool, handles errors and logs.
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            pool = await self.get_pool()
            if pool is None:
                logger.error("[DB] Failed to get connection pool")
                return None

            # Call original function with pool
            return await func(self, pool, *args, **kwargs)

        except Exception as e:
            logger.error(f"[DB] Error in {func.__name__}: {e}")
            return None

    return wrapper
