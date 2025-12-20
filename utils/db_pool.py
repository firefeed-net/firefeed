# utils/db_pool.py - Database pool management utilities
import logging
from di_container import get_service

logger = logging.getLogger(__name__)


async def get_db_pool():
    """Getting shared DB pool"""
    try:
        config_obj = get_service(dict)
        pool = await config_obj.get('get_shared_db_pool')()
        return pool
    except Exception as e:
        logger.info(f"[DB] Error getting PostgreSQL connection pool: {e}")
        return None


async def close_db_pool():
    """Closes the shared database connection pool."""
    try:
        config_obj = get_service(dict)
        await config_obj.get('close_shared_db_pool')()
        logger.info("[DB] Shared PostgreSQL connection pool closed.")
    except Exception as e:
        logger.info(f"[DB] Error closing PostgreSQL connection pool: {e}")