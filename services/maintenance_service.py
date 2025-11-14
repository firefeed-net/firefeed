# services/maintenance_service.py
import logging
from interfaces import IMaintenanceService
from config import get_shared_db_pool

logger = logging.getLogger(__name__)


class MaintenanceService(IMaintenanceService):
    """Service for maintenance operations like cleanup"""

    async def cleanup_duplicates(self) -> None:
        """Clean up duplicate RSS items from database"""
        try:
            pool = await get_shared_db_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Find and delete duplicate groups based on embedding similarity
                    await cur.execute(
                        """
                        WITH duplicate_groups AS (
                            SELECT
                                news_id,
                                ROW_NUMBER() OVER (PARTITION BY embedding ORDER BY created_at) as rn
                            FROM published_news_data
                            WHERE embedding IS NOT NULL
                            GROUP BY news_id, embedding, created_at
                            HAVING COUNT(*) > 1
                        )
                        DELETE FROM published_news_data
                        WHERE news_id IN (
                            SELECT news_id FROM duplicate_groups WHERE rn > 1
                        )
                    """

                    )

                    deleted_count = cur.rowcount
                    logger.info(f"[CLEANUP] Deleted {deleted_count} duplicate entries")

        except Exception as e:
            logger.error(f"[CLEANUP] Error during duplicate cleanup: {e}")
            raise