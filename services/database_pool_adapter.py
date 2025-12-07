# services/database_pool_adapter.py
import logging
from contextlib import asynccontextmanager
from interfaces import IDatabasePool

logger = logging.getLogger(__name__)


class DatabasePoolAdapter(IDatabasePool):
    """Adapter for the shared database pool to implement IDatabasePool interface"""

    def __init__(self, db_pool):
        self._pool = db_pool

    @asynccontextmanager
    async def acquire(self):
        """Acquire database connection"""
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            self._pool.release(conn)

    async def close(self) -> None:
        """Close pool - handled by config.py"""
        # The pool is managed globally by config.py
        pass