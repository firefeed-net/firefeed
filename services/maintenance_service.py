# services/maintenance_service.py
import logging
from typing import Dict, Any
from interfaces import IMaintenanceService
from exceptions import DatabaseException, ServiceUnavailableException

logger = logging.getLogger(__name__)


class MaintenanceService(IMaintenanceService):
    """Service for maintenance operations like cleanup"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def cleanup_duplicates(self) -> None:
        """Clean up duplicate RSS items from database"""
        try:
            async with self.db_pool.acquire() as conn:
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
            raise DatabaseException(f"Error during duplicate cleanup: {str(e)}")

    async def cleanup_old_data_by_age(self, hours_old: int) -> Dict[str, Any]:
        """Atomic full cleanup of old data by age: news, translations, publications, files"""
        try:
            from repositories.rss_item_repository import RSSItemRepository
            import os

            # Get repository via DI or create instance
            rss_repo = RSSItemRepository(self.db_pool)

            # Atomic database data cleanup
            deleted_count, files_to_delete, db_cleanup_success = await rss_repo.cleanup_old_rss_items(hours_old)

            if not db_cleanup_success:
                raise DatabaseException("Failed to perform database cleanup")

            # After successful transaction commit - clean up files
            images_deleted = 0
            videos_deleted = 0
            files_failed = 0

            config = get_service_config()

            for image_file, video_file in files_to_delete:
                # Delete image
                if image_file and config.images_root_dir:
                    image_path = os.path.join(config.images_root_dir, image_file)
                    try:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                            images_deleted += 1
                    except Exception as e:
                        logger.error(f"[CLEANUP] Error deleting image {image_path}: {e}")
                        files_failed += 1

                # Delete video
                if video_file and config.videos_root_dir:
                    video_path = os.path.join(config.videos_root_dir, video_file)
                    try:
                        if os.path.exists(video_path):
                            os.remove(video_path)
                            videos_deleted += 1
                    except Exception as e:
                        logger.error(f"[CLEANUP] Error deleting video {video_path}: {e}")
                        files_failed += 1

            result = {
                "news_items_deleted": deleted_count,
                "translations_deleted": "included in transaction",  # Translations are deleted in the same transaction
                "telegram_publications_deleted": "included in transaction",  # Publications are deleted in the same transaction
                "images_deleted": images_deleted,
                "videos_deleted": videos_deleted,
                "files_failed_to_delete": files_failed,
                "cleanup_interval_hours": hours_old,
                "transaction_success": True
            }

            logger.info(f"[CLEANUP] Atomic full cleanup completed successfully: {result}")
            return result

        except Exception as e:
            raise ServiceUnavailableException("maintenance", f"Critical error during atomic cleanup: {str(e)}")