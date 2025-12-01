import asyncio
import signal
import sys
import time
import logging
from logging_config import setup_logging
from services.rss import RSSManager
from di_container import setup_di_container, get_service
from interfaces import (
    IDuplicateDetector, ITranslationService, ITranslatorQueue,
    IRSSFetcher, IRSSValidator, IRSSStorage, IMediaExtractor, IMaintenanceService
)
from config import close_shared_db_pool

setup_logging()
logger = logging.getLogger(__name__)


class RSSParserService:
    def __init__(self):
        # Initialize DI container
        setup_di_container()

        # Get services via DI
        self.duplicate_detector = get_service(IDuplicateDetector)
        self.translation_service = get_service(ITranslationService)
        self.translator_queue = get_service(ITranslatorQueue)
        self.rss_fetcher = get_service(IRSSFetcher)
        self.rss_validator = get_service(IRSSValidator)
        self.rss_storage = get_service(IRSSStorage)
        self.media_extractor = get_service(IMediaExtractor)
        self.maintenance_service = get_service(IMaintenanceService)

        # Create RSSManager via DI (it will get all dependencies automatically)
        from services.rss.rss_manager import RSSManager
        self.rss_manager = RSSManager(
            rss_fetcher=self.rss_fetcher,
            rss_validator=self.rss_validator,
            rss_storage=self.rss_storage,
            media_extractor=self.media_extractor,
            translation_service=self.translation_service,
            duplicate_detector=self.duplicate_detector,
            translator_queue=self.translator_queue,
            maintenance_service=self.maintenance_service
        )
        self.running = True
        self.parse_task = None
        self.batch_processor_task = None
        self.cleanup_task = None

    async def parse_rss_task(self):
        """Periodic RSS parsing task"""
        while self.running:
            try:
                logger.info("[RSS_PARSER] Starting RSS feeds parsing...")
                result = await self.rss_manager.process_all_feeds()
                logger.info(f"[RSS_PARSER] RSS feeds parsing completed: {result}")

                # Unload unused translation models to free memory
                unloaded = await self.translation_service.model_manager.unload_unused_models(max_age_seconds=1800)
                logger.info(f"[RSS_PARSER] Unloaded {unloaded} unused translation models after parsing")

                # Wait 3 minutes before next parsing or until self.running = False is set
                for _ in range(180):
                    if not self.running:
                        logger.info("[RSS_PARSER] [PARSE_TASK] Stop signal received, terminating parsing task.")
                        return
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("[RSS_PARSER] [PARSE_TASK] Parsing task cancelled")
                break
            except Exception as e:
                logger.error(f"[RSS_PARSER] [PARSE_TASK] Parsing error: {e}")
                import traceback

                traceback.print_exc()
                # Reduce wait time before retry or checking stop flag
                for _ in range(30):  # 30 seconds
                    if not self.running:
                        logger.info(
                            "[RSS_PARSER] [PARSE_TASK] Stop signal received during wait, terminating parsing task."
                        )
                        return
                    await asyncio.sleep(1)

    async def batch_processor_job(self):
        """Regular batch processing task"""
        try:
            logger.info("[BATCH] Starting regular batch processing of news without embeddings...")
            # Use new duplicate detector interface
            if hasattr(self.duplicate_detector, 'process_missing_embeddings_batch'):
                success, errors = await self.duplicate_detector.process_missing_embeddings_batch(
                    batch_size=20, delay_between_items=0.2
                )
                logger.info(f"[BATCH] Regular batch processing completed. Successful: {success}, Errors: {errors}")
            else:
                logger.warning("[BATCH] Duplicate detector does not support batch embedding processing")
        except Exception as e:
            logger.error(f"[ERROR] [BATCH] Error in regular batch processing: {e}")
            import traceback

            traceback.print_exc()

    async def cleanup_duplicates_task(self):
        """Background duplicate cleanup task (runs every hour)"""
        while self.running:
            try:
                logger.info("[CLEANUP] Starting periodic duplicate cleanup...")
                await self.rss_manager.cleanup_duplicates()
                logger.info("[CLEANUP] Periodic duplicate cleanup completed")

                # Wait 1 hour before next cleanup or until stop
                for _ in range(3600):
                    if not self.running:
                        logger.info(
                            "[RSS_PARSER] [CLEANUP_TASK] Stop signal received, terminating duplicate cleanup task."
                        )
                        return
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("[CLEANUP] [CLEANUP_TASK] Duplicate cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"[CLEANUP] [CLEANUP_TASK] Error in background duplicate cleanup task: {e}")
                import traceback

                traceback.print_exc()
                # Wait 5 minutes before retry or checking stop flag
                for _ in range(300):
                    if not self.running:
                        logger.info(
                            "[RSS_PARSER] [CLEANUP_TASK] Stop signal received during wait, terminating duplicate cleanup task."
                        )
                        return
                    await asyncio.sleep(1)

    async def batch_processor_task_loop(self):
        """Background batch processing task"""
        while self.running:
            try:
                await self.batch_processor_job()
                # Wait 30 minutes before next batch processing or until stop
                for _ in range(1800):
                    if not self.running:
                        logger.info(
                            "[RSS_PARSER] [BATCH_TASK] Stop signal received, terminating batch processing task."
                        )
                        return
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("[BATCH] [BATCH_TASK] Batch processing task cancelled")
                break
            except Exception as e:
                logger.error(f"[BATCH] [BATCH_TASK] Error in background batch processing task: {e}")
                import traceback

                traceback.print_exc()
                # Wait a minute before retry or checking stop flag
                for _ in range(60):
                    if not self.running:
                        logger.info(
                            "[RSS_PARSER] [BATCH_TASK] Stop signal received during wait, terminating batch processing task."
                        )
                        return
                    await asyncio.sleep(1)

    async def start(self):
        """Starting the parsing service"""
        logger.info("[RSS_PARSER] Starting RSS parsing service...")

        # Register asynchronous signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._signal_handler(s)))

        # Start translation queue via DI service
        if hasattr(self.translator_queue, 'start'):
            await self.translator_queue.start()
            logger.info("[RSS_PARSER] Translation queue started via DI")
        else:
            logger.warning("[RSS_PARSER] Translator queue does not have start method")

        # Preload popular translation models to reduce I/O during runtime
        try:
            await self.translation_service.model_manager.preload_popular_models()
            logger.info("[RSS_PARSER] Popular translation models preloaded successfully")
        except Exception as e:
            logger.error(f"[RSS_PARSER] Error preloading translation models: {e}")

        # Create tasks
        self.parse_task = asyncio.create_task(self.parse_rss_task())
        self.batch_processor_task = asyncio.create_task(self.batch_processor_task_loop())
        self.cleanup_task = asyncio.create_task(self.cleanup_duplicates_task())

        try:
            # Wait for any task to complete (usually doesn't happen if running=True)
            # Or completion by signal (which sets running=False and tasks will complete)
            done, pending = await asyncio.wait(
                [self.parse_task, self.batch_processor_task, self.cleanup_task], return_when=asyncio.FIRST_COMPLETED
            )
            logger.info(f"[RSS_PARSER] One of the tasks completed. Done: {len(done)}, Pending: {len(pending)}")

            # Cancel remaining tasks
            for task in pending:
                if not task.done():
                    logger.info(
                        f"[RSS_PARSER] Cancelling remaining task {task.get_name() if hasattr(task, 'get_name') else 'Unknown'}..."
                    )
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info(
                            f"[RSS_PARSER] Task {task.get_name() if hasattr(task, 'get_name') else 'Unknown'} successfully cancelled"
                        )
                    except Exception as e:
                        logger.error(f"[RSS_PARSER] Error cancelling task: {e}")

        except Exception as e:
            logger.error(f"[RSS_PARSER] Critical error in start(): {e}")
            import traceback

            traceback.print_exc()
        finally:
            await self.cleanup()

    async def _signal_handler(self, signum):
        """Asynchronous signal handler for termination"""
        sig_name = signal.Signals(signum).name
        logger.info(f"[RSS_PARSER] Received signal {sig_name} ({signum})")
        self.running = False

        # If SIGTERM signal, give some time for proper shutdown
        # If SIGINT (Ctrl+C), can stop faster
        # But in any case, main shutdown logic is in cleanup()
        if signum == signal.SIGTERM:
            logger.info("[RSS_PARSER] Waiting for current operations to complete (up to 10 seconds)...")
            try:
                # Wait a bit so tasks can complete by self.running flag
                await asyncio.wait_for(asyncio.shield(self._wait_for_tasks_to_stop()), timeout=10.0)
            except asyncio.TimeoutError:
                logger.info("[RSS_PARSER] Timeout waiting for tasks to complete. Continuing shutdown.")
        # For SIGINT, continue

    async def _wait_for_tasks_to_stop(self):
        """Helper function to wait for tasks to stop"""
        # Wait until tasks complete themselves via self.running=False
        # This is needed for use with wait_for
        while (
            (self.parse_task and not self.parse_task.done())
            or (self.batch_processor_task and not self.batch_processor_task.done())
            or (self.cleanup_task and not self.cleanup_task.done())
        ):
            await asyncio.sleep(0.1)
        logger.info("[RSS_PARSER] All tasks stopped by running flag.")

    async def cleanup(self):
        """Resource cleanup"""
        logger.info("[RSS_PARSER] Starting resource cleanup...")
        self.running = False  # Make sure the stop flag is set

        # --- Stopping tasks ---
        tasks_to_cancel = []
        if self.parse_task and not self.parse_task.done():
            logger.info("[RSS_PARSER] Cancelling active parsing task...")
            self.parse_task.cancel()
            tasks_to_cancel.append(self.parse_task)

        if self.batch_processor_task and not self.batch_processor_task.done():
            logger.info("[RSS_PARSER] Cancelling active batch processing task...")
            self.batch_processor_task.cancel()
            tasks_to_cancel.append(self.batch_processor_task)

        if self.cleanup_task and not self.cleanup_task.done():
            logger.info("[RSS_PARSER] Cancelling active duplicate cleanup task...")
            self.cleanup_task.cancel()
            tasks_to_cancel.append(self.cleanup_task)

        # Wait for cancelled tasks to complete
        if tasks_to_cancel:
            logger.info(f"[RSS_PARSER] Waiting for {len(tasks_to_cancel)} cancelled tasks to complete...")
            done, pending = await asyncio.wait(tasks_to_cancel, timeout=5.0)  # Timeout 5 seconds
            if pending:
                logger.warning(f"[RSS_PARSER] Warning: {len(pending)} tasks did not complete within timeout.")
            else:
                logger.info("[RSS_PARSER] All tasks successfully cancelled.")

        # --- Stopping translation queue via DI ---
        if hasattr(self, "translator_queue") and self.translator_queue:
            logger.info("[RSS_PARSER] Stopping translation queue via DI...")
            try:
                # Stop queue via DI service
                if hasattr(self.translator_queue, 'stop'):
                    await self.translator_queue.stop()
                    logger.info("[RSS_PARSER] Translation queue stopped via DI.")
                else:
                    logger.warning("[RSS_PARSER] Translator queue does not have stop method")
            except Exception as e:
                logger.error(f"[RSS_PARSER] Error stopping translation queue via DI: {e}")
                import traceback

                traceback.print_exc()

            # ------------------------------------

        # Close managers (stubs, but leave them)
        managers_to_close = [(self.rss_manager, "RSSManager"), (self.duplicate_detector, "FireFeedDuplicateDetector")]

        for manager, name in managers_to_close:
            try:
                if hasattr(manager, "close_pool"):
                    await manager.close_pool()
                    logger.info(f"[RSS_PARSER] Manager {name} closed (stub)")
            except Exception as e:
                logger.error(f"[RSS_PARSER] Error closing manager {name}: {e}")

        # Unload all unused models before shutdown
        try:
            unloaded = await self.translation_service.model_manager.unload_unused_models(max_age_seconds=0)
            logger.info(f"[RSS_PARSER] Unloaded {unloaded} models before shutdown")
        except Exception as e:
            logger.error(f"[RSS_PARSER] Error unloading models during cleanup: {e}")

        # Close shared connection pool
        try:
            await close_shared_db_pool()
            logger.info("[RSS_PARSER] Shared connection pool closed")
        except Exception as e:
            logger.error(f"[RSS_PARSER] Error closing shared pool: {e}")

        logger.info("[RSS_PARSER] Resource cleanup completed.")


async def main():
    """Asynchronous entry point"""
    service = None
    try:
        service = RSSParserService()
        await service.start()
    except KeyboardInterrupt:
        logger.info("[RSS_PARSER] [MAIN] Service interrupted by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"[RSS_PARSER] [MAIN] Critical error in main loop: {e}")
        import traceback

        traceback.print_exc()
    # finally not needed, since cleanup is called inside start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[RSS_PARSER] [ENTRY] Application stopped by user")
    except Exception as e:
        logger.error(f"[RSS_PARSER] [ENTRY] Fatal application error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
