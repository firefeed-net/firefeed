# services/database_pool_adapter.py
import logging
from contextlib import asynccontextmanager
from interfaces import IDatabasePool
from config import get_shared_db_pool

logger = logging.getLogger(__name__)


class DatabasePoolAdapter(IDatabasePool):
    """Adapter for the shared database pool to implement IDatabasePool interface"""

    def __init__(self):
        self._pool = None

    @asynccontextmanager
    async def acquire(self):
        """Acquire database connection"""
        if self._pool is None:
            self._pool = await get_shared_db_pool()
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            self._pool.release(conn)

    async def close(self) -> None:
        """Close pool - handled by config.py"""
        # The pool is managed globally by config.py
        pass