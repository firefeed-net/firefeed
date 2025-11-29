import asyncio
from asyncio import Queue
import time
import logging

logger = logging.getLogger(__name__)


class FireFeedTranslatorTaskQueue:
    def __init__(self, translator=None, max_workers=1, queue_size=30):
        self.translator = translator
        self.queue = Queue(maxsize=queue_size)
        self.max_workers = max_workers
        self.workers = []
        self.running = False
        self.stats = {"processed": 0, "errors": 0, "queued": 0}

    def set_translator(self, translator):
        """Set translator instance (for DI compatibility)"""
        self.translator = translator

    async def start(self):
        """Start task queue"""
        self.running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        logger.info(f"[QUEUE] 🔧 Started {self.max_workers} translation worker threads")

    async def _worker(self, worker_id):
        """Worker thread for processing tasks"""
        while self.running:
            try:
                # Get task with timeout
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                start_time = time.time()
                task_id = task.get("task_id", "unknown")
                logger.info(f"[{worker_id}] 📥 Starting task processing: {task_id[:20]}")

                try:
                    # Prepare target languages (all except original)
                    target_langs = ["en", "ru", "de", "fr"]  # TODO: make configurable
                    original_lang = task["data"]["original_lang"]
                    if original_lang in target_langs:
                        target_langs.remove(original_lang)

                    # Call translator without callback parameters
                    result = await self.translator.prepare_translations(
                        title=task["data"]["title"],
                        content=task["data"]["content"],
                        original_lang=original_lang,
                        target_langs=target_langs
                    )

                    # Call success callback if provided
                    if task.get("callback"):
                        try:
                            await task["callback"](result, task_id=task_id)
                        except Exception as callback_error:
                            logger.error(f"[{worker_id}] ❌ Error in callback for task {task_id[:20]}: {callback_error}")

                    # Statistics
                    self.stats["processed"] += 1

                    duration = time.time() - start_time
                    logger.info(f"[{worker_id}] ✅ Task {task_id[:20]} completed in {duration:.2f} sec")
                except Exception as e:
                    # Call error callback if provided
                    if task.get("error_callback"):
                        try:
                            await task["error_callback"]({"error": str(e), "task_id": task_id}, task_id=task_id)
                        except Exception as callback_error:
                            logger.error(f"[{worker_id}] ❌ Error in error_callback for task {task_id[:20]}: {callback_error}")

                    # Error statistics
                    self.stats["errors"] += 1
                    logger.error(f"[{worker_id}] ❌ Translation error for task {task_id[:20]}: {e}")

                finally:
                    self.queue.task_done()
            except asyncio.TimeoutError:
                # Continue loop if timeout
                continue
            except Exception as e:
                logger.error(f"[{worker_id}] ❌ Critical worker error: {e}")
                # traceback.print_exc() # Removed, as the error above is already logged
                if not self.queue.empty():
                    self.queue.task_done()

    async def add_task(self, title, content, original_lang, callback=None, error_callback=None, task_id=None):
        """Adding translation task to queue"""
        if self.translator is None:
            logger.error("[QUEUE] ❌ Translator not set, cannot add task")
            return False

        task = {
            "data": {"title": title, "content": content, "original_lang": original_lang},
            "callback": callback,
            "error_callback": error_callback,
            "task_id": task_id,
        }

        try:
            await self.queue.put(task)
            self.stats["queued"] += 1
            logger.info(f"[QUEUE] 📨 Translation task added (in queue: {self.queue.qsize()})")
            return True
        except asyncio.QueueFull:
            logger.warning("⚠️ [QUEUE] Translation queue is full!")
            return False

    async def wait_completion(self):
        """Waiting for all tasks in queue to complete"""
        if self.queue.qsize() > 0:
            logger.info(f"[QUEUE] ⏳ Waiting for {self.queue.qsize()} tasks to complete...")
            await self.queue.join()
            logger.info("[QUEUE] ✅ All tasks completed")

    async def stop(self):
        """Stopping the queue"""
        logger.info("[QUEUE] 🛑 Stopping task queue...")
        self.running = False

        # Cancel all worker threads
        for worker in self.workers:
            if not worker.done():
                worker.cancel()

        # Wait for completion with timeout
        try:
            await asyncio.wait_for(asyncio.gather(*self.workers, return_exceptions=True), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("[QUEUE] ⚠️ Force stopping workers")

        logger.info("[QUEUE] ✅ Task queue stopped")

    def get_stats(self):
        """Getting queue statistics"""
        return self.stats.copy()

    def print_stats(self):
        """Output statistics"""
        stats = self.get_stats()
        logger.info(f"[QUEUE] 📊 Statistics:")
        logger.info(f"  Processed: {stats['processed']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info(f"  In queue: {stats['queued']}")
        if stats["processed"] + stats["errors"] > 0:
            success_rate = (stats["processed"] / (stats["processed"] + stats["errors"])) * 100
            logger.info(f"  Success rate: {success_rate:.1f}%")