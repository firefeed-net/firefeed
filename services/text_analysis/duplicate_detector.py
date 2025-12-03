import asyncio
import json
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging
from config import RSS_ITEM_SIMILARITY_THRESHOLD
from utils.database import DatabaseMixin
from services.text_analysis.embeddings_processor import FireFeedEmbeddingsProcessor
from config_services import get_service_config

logger = logging.getLogger(__name__)


class FireFeedDuplicateDetector(DatabaseMixin):
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: str = "cpu",
        similarity_threshold: float = RSS_ITEM_SIMILARITY_THRESHOLD,
    ):
        """
        Initialization of asynchronous news duplicate detector

        Args:
            model_name: Name of the sentence-transformers model
            device: Device for the model
            similarity_threshold: Base similarity threshold
        """
        if model_name is None:
            config = get_service_config()
            model_name = config.deduplication.embedding_models.sentence_transformer_model
        self.processor = FireFeedEmbeddingsProcessor(model_name, device)
        self.similarity_threshold = similarity_threshold

    async def _combine_text_fields(self, title: str, content: str, lang_code: str = "en") -> str:
        """Combining title and content for embedding creation"""
        return await self.processor.combine_texts(title, content, lang_code)

    async def _get_embedding_by_id(self, rss_item_id: str) -> Optional[List[float]]:
        """Getting existing embedding by RSS item ID"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT embedding
                    FROM published_news_data
                    WHERE news_id = %s AND embedding IS NOT NULL
                """,
                    (rss_item_id,),
                )

                result = await cur.fetchone()
                if result and result[0] is not None:
                    # Convert from string to list if needed
                    if isinstance(result[0], str):
                        return json.loads(result[0])
                    return result[0]
                return None

    async def _is_duplicate_with_embedding(
        self, rss_item_id: str, embedding: List[float], text_length: int = 0, text_type: str = "content"
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Checking duplicate with existing embedding"""
        try:
            pool = await self.get_pool()
            # Search for similar RSS items, excluding current
            similar_rss_items = await self.get_similar_rss_items(embedding, current_rss_item_id=rss_item_id, limit=5, pool=pool)

            # Dynamic threshold
            threshold = self.processor.get_dynamic_threshold(text_length, text_type)

            # Check similarity
            for rss_item in similar_rss_items:
                if rss_item["embedding"] is not None:
                    # Convert embedding
                    try:
                        if isinstance(rss_item["embedding"], str):
                            stored_embedding = json.loads(rss_item["embedding"])
                        elif isinstance(rss_item["embedding"], (list, np.ndarray)):
                            stored_embedding = (
                                list(rss_item["embedding"])
                                if isinstance(rss_item["embedding"], np.ndarray)
                                else rss_item["embedding"]
                            )
                        else:
                            continue
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"[DUPLICATE_DETECTOR] Error converting embedding from DB: {e}")
                        continue

                    similarity = await self.processor.calculate_similarity(stored_embedding, embedding)

                    if similarity > threshold:
                        logger.info(
                            f"[DUPLICATE_DETECTOR] Duplicate found with similarity {similarity:.4f} (threshold: {threshold:.4f})"
                        )
                        return True, rss_item

            return False, None

        except Exception as e:
            logger.error(f"[DUPLICATE_DETECTOR] Error checking duplicate with embedding: {e}")
            raise

    async def generate_embedding(self, title: str, content: str, lang_code: str = "en") -> List[float]:
        """
        Generating embedding for RSS item

        Args:
            title: RSS item title
            content: RSS item content
            lang_code: Language code

        Returns:
            RSS item embedding as list of float
        """
        combined_text = await self._combine_text_fields(title, content, lang_code)
        return await self.processor.generate_embedding(combined_text, lang_code)

    async def save_embedding(self, rss_item_id: str, embedding: List[float]):
        """
        Saving embedding to database

        Args:
            rss_item_id: RSS item ID
            embedding: RSS item embedding
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE published_news_data
                    SET embedding = %s
                    WHERE news_id = %s
                """,
                    (embedding, rss_item_id),
                )
                # Remove await conn.commit() - transactions are managed automatically in aiopg
                logger.debug(f"Embedding for RSS item {rss_item_id} successfully saved")

    async def get_similar_rss_items(
        self, embedding: List[float], current_rss_item_id: str = None, limit: int = 10, pool=None
    ) -> List[Dict[str, Any]]:
        """
        Searching for similar RSS items in the database

        Args:
            embedding: Embedding for search
            current_rss_item_id: ID of the current RSS item (to exclude it from results)
            limit: Maximum number of results
            pool: Connection pool (optional, for reuse)

        Returns:
            List of similar RSS items
        """
        try:
            # Use provided pool or get new one
            if pool is None:
                pool = await self.get_pool()

            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    if current_rss_item_id:
                        # Exclude current RSS item from search
                        await cur.execute(
                            """
                            SELECT news_id, original_title, original_content, embedding
                            FROM published_news_data
                            WHERE embedding IS NOT NULL
                            AND news_id != %s
                            ORDER BY embedding <-> %s::vector
                            LIMIT %s
                        """,
                            (current_rss_item_id, embedding, limit),
                        )
                    else:
                        # If ID not provided, search among all RSS items
                        await cur.execute(
                            """
                            SELECT news_id, original_title, original_content, embedding
                            FROM published_news_data
                            WHERE embedding IS NOT NULL
                            ORDER BY embedding <-> %s::vector
                            LIMIT %s
                        """,
                            (embedding, limit),
                        )

                    results = await cur.fetchall()
                    return [dict(zip([column[0] for column in cur.description], row)) for row in results]
        except Exception as e:
            logger.error(f"[DUPLICATE_DETECTOR] Error searching for similar RSS items: {e}")
            raise

    async def is_duplicate(
        self, title: str, content: str, link: str, lang_code: str = "en"
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checking if RSS item is a duplicate

        Args:
            title: RSS item title
            content: RSS item content
            link: RSS item link
            lang_code: Language code

        Returns:
            Tuple: (is_duplicate, duplicate_info)
        """
        try:
            # First check by URL (if link matches - definitely duplicate)
            if link:
                try:
                    pool = await self.get_pool()
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """
                                SELECT news_id, original_title
                                FROM published_news_data
                                WHERE source_url = %s AND source_url IS NOT NULL
                                LIMIT 1
                                """,
                                (link,),
                            )

                            result = await cur.fetchone()
                            if result:
                                return True, {"news_id": result[0], "title": result[1], "reason": "same_url"}

                except Exception as e:
                    logger.error(f"Error checking by URL: {e}")

            # Generate embedding for new RSS item
            embedding = await self.generate_embedding(title, content, lang_code)

            # Search for similar RSS items (without excluding current, since it doesn't exist yet)
            similar_rss_items = await self.get_similar_rss_items(embedding, limit=5)

            # Text length for dynamic threshold
            text_length = len(title) + len(content)
            threshold = self.processor.get_dynamic_threshold(text_length, "content")

            # Check similarity
            for rss_item in similar_rss_items:
                if rss_item["embedding"] is not None:
                    # Convert embedding
                    try:
                        if isinstance(rss_item["embedding"], str):
                            stored_embedding = json.loads(rss_item["embedding"])
                        elif isinstance(rss_item["embedding"], (list, np.ndarray)):
                            stored_embedding = (
                                list(rss_item["embedding"])
                                if isinstance(rss_item["embedding"], np.ndarray)
                                else rss_item["embedding"]
                            )
                        else:
                            logger.warning(
                                f"[DUPLICATE_DETECTOR] Unknown data type for embedding: {type(rss_item['embedding'])}"
                            )
                            continue
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"[DUPLICATE_DETECTOR] Error converting embedding from DB: {e}")
                        continue

                    similarity = await self.processor.calculate_similarity(stored_embedding, embedding)

                    if similarity > threshold:
                        logger.info(
                            f"[DUPLICATE_DETECTOR] Duplicate found with similarity {similarity:.4f} (threshold: {threshold:.4f})"
                        )
                        return True, rss_item

            return False, None

        except Exception as e:
            logger.error(f"[DUPLICATE_DETECTOR] Error checking duplicate: {e}")
            raise


    async def process_rss_item(self, rss_item_id: str, title: str, content: str, lang_code: str = "en") -> bool:
        """
        Full processing of RSS item: duplicate check and embedding saving

        Args:
            rss_item_id: RSS item ID
            title: RSS item title
            content: RSS item content
            lang_code: Language code

        Returns:
            True if RSS item is unique, False if duplicate
        """
        try:
            # First check if embedding already exists for this RSS item
            existing_embedding = await self._get_embedding_by_id(rss_item_id)

            text_length = len(title) + len(content)

            # If embedding already exists, use it for duplicate checking
            if existing_embedding is not None:
                logger.debug(f"[DUPLICATE_DETECTOR] Embedding for RSS item {rss_item_id} already exists")
                # Check for duplicate using existing embedding
                is_dup, duplicate_info = await self._is_duplicate_with_embedding(
                    rss_item_id, existing_embedding, text_length, "content"
                )
            else:
                # If no embedding, generate new one
                logger.debug(f"[DUPLICATE_DETECTOR] Generating new embedding for RSS item {rss_item_id}")
                embedding = await self.generate_embedding(title, content, lang_code)

                # Check for duplicate with new embedding
                is_dup, duplicate_info = await self._is_duplicate_with_embedding(
                    rss_item_id, embedding, text_length, "content"
                )

                # If not duplicate, save embedding
                if not is_dup:
                    await self.save_embedding(rss_item_id, embedding)

            if is_dup:
                logger.info(
                    f"[DUPLICATE_DETECTOR] RSS item {title[:50]} is a duplicate of RSS item {duplicate_info['news_id']}"
                )
                return False

            # logger.info(f"[DUPLICATE_DETECTOR] RSS item {rss_item_id} is unique")
            return True

        except Exception as e:
            logger.error(f"[DUPLICATE_DETECTOR] Error processing RSS item {rss_item_id}: {e}")
            raise

    # --- Methods for batch processing ---

    async def get_rss_items_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Gets list of RSS items without embeddings from database (asynchronously).

        Args:
            limit: Maximum number of RSS items to retrieve.

        Returns:
            List of dictionaries with RSS item data (news_id, original_title, original_content).
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:

                query = """
                    SELECT news_id, original_title, original_content
                    FROM published_news_data
                    WHERE embedding IS NULL
                    ORDER BY created_at ASC -- Process oldest records first
                    LIMIT %s
                """
                await cur.execute(query, (limit,))
                results = await cur.fetchall()

                # Get column names
                # cur.description available after execute
                column_names = [desc[0] for desc in cur.description]

                # Convert results to list of dictionaries
                rss_items_list = [dict(zip(column_names, row)) for row in results]

                logger.info(f"[BATCH_EMBEDDING] Retrieved {len(rss_items_list)} RSS items without embeddings.")
                return rss_items_list

    async def process_single_rss_item_batch(self, rss_item: Dict[str, Any], lang_code: str = "en") -> bool:
        """
        Asynchronously processes one RSS item in batch processing:
        generates and saves embedding.

        Args:
            rss_item: Dictionary with RSS item data (news_id, original_title, original_content).
            lang_code: Language code

        Returns:
            True if embedding saved successfully, False on error.
        """
        rss_item_id = rss_item["news_id"]
        title = rss_item["original_title"]
        content = rss_item["original_content"]

        try:
            logger.debug(f"[BATCH_EMBEDDING] Starting processing of RSS item {rss_item_id}...")

            # 1. Generate embedding
            embedding = await self.generate_embedding(title, content, lang_code)
            logger.debug(f"[BATCH_EMBEDDING] Embedding for {rss_item_id} generated.")

            # 2. Save embedding
            await self.save_embedding(rss_item_id, embedding)
            logger.info(f"[BATCH_EMBEDDING] Embedding for RSS item {rss_item_id} successfully saved.")
            return True

        except Exception as e:
            logger.error(f"[BATCH_EMBEDDING] Error processing RSS item {rss_item_id}: {e}", exc_info=True)
            return False

    async def process_missing_embeddings_batch(
        self, batch_size: int = 50, delay_between_items: float = 0.1
    ) -> Tuple[int, int]:
        """
        Asynchronously processes one batch of RSS items without embeddings.

        Args:
            batch_size: Number of RSS items to process in one "run".
            delay_between_items: Delay (in seconds) between processing each RSS item
                                within batch to reduce load.

        Returns:
            Tuple (successfully processed, errors).
        """
        logger.info(f"[BATCH_EMBEDDING] Starting batch processing: batch size {batch_size}.")

        # 1. Get list of RSS items without embeddings (asynchronously)
        try:
            rss_items_without_embeddings = await self.get_rss_items_without_embeddings(limit=batch_size)
        except Exception as e:
            logger.error(f"[BATCH_EMBEDDING] Failed to retrieve RSS items list: {e}")
            return 0, 0  # Return 0, 0 on list retrieval error

        if not rss_items_without_embeddings:
            logger.info("[BATCH_EMBEDDING] No RSS items without embeddings found.")
            return 0, 0

        logger.info(f"[BATCH_EMBEDDING] Found {len(rss_items_without_embeddings)} RSS items for processing.")

        success_count = 0
        error_count = 0

        # 3. Process each RSS item in batch
        for i, rss_item in enumerate(rss_items_without_embeddings):
            rss_item_id = rss_item["news_id"]
            logger.debug(f"[BATCH_EMBEDDING] Processing RSS item {i+1}/{len(rss_items_without_embeddings)}: {rss_item_id}")

            success = await self.process_single_rss_item_batch(rss_item)
            if success:
                success_count += 1
            else:
                error_count += 1

            # Add small delay between processing RSS items in batch
            if delay_between_items > 0 and (i + 1) < len(rss_items_without_embeddings):
                await asyncio.sleep(delay_between_items)

        logger.info(f"[BATCH_EMBEDDING] Batch processed. Successful: {success_count}, Errors: {error_count}")

        # Unload unused models after batch embedding processing
        try:
            unloaded = await self.processor.model_manager.unload_unused_models(max_age_seconds=1800)
            logger.info(f"[BATCH_EMBEDDING] Unloaded {unloaded} unused models after batch processing")
        except Exception as e:
            logger.error(f"[BATCH_EMBEDDING] Error unloading models: {e}")

        return success_count, error_count

    async def run_batch_processor_continuously(
        self, batch_size: int = 50, delay_between_batches: float = 60.0, delay_between_items: float = 0.1
    ):
        """
        Starts continuous batch processing of RSS items without embeddings on schedule.

        Args:
            batch_size: Number of RSS items to process in one "run".
            delay_between_batches: Delay (in seconds) between processing batches.
            delay_between_items: Delay (in seconds) between processing each RSS item within batch.
        """
        logger.info("[BATCH_EMBEDDING] Starting continuous batch processing...")
        while True:
            try:
                success, errors = await self.process_missing_embeddings_batch(
                    batch_size=batch_size, delay_between_items=delay_between_items
                )
                # Even if 0 news processed, still wait before next iteration
                logger.debug(f"[BATCH_EMBEDDING] Waiting {delay_between_batches} seconds until next batch...")
                await asyncio.sleep(delay_between_batches)

            except asyncio.CancelledError:
                logger.info("[BATCH_EMBEDDING] Continuous batch processing cancelled.")
                break  # Exit loop on cancellation
            except Exception as e:
                logger.error(f"[BATCH_EMBEDDING] Unexpected error in continuous processing: {e}", exc_info=True)
                # Wait before retry in case of error
                logger.debug(f"[BATCH_EMBEDDING] Waiting {delay_between_batches} seconds before retry...")
                await asyncio.sleep(delay_between_batches)

    async def run_batch_processor_once(
        self, batch_size: int = 100, delay_between_items: float = 0.1
    ) -> Tuple[int, int]:
        """
        Starts batch processing once.

        Args:
            batch_size: Number of RSS items to process.
            delay_between_items: Delay (in seconds) between processing each RSS item.

        Returns:
            Tuple (successfully processed, errors).
        """
        logger.info("[BATCH_EMBEDDING] Starting one-time batch processing...")
        try:
            success, errors = await self.process_missing_embeddings_batch(
                batch_size=batch_size, delay_between_items=delay_between_items
            )
            logger.info(f"[BATCH_EMBEDDING] One-time processing completed. Successful: {success}, Errors: {errors}")
            return success, errors
        except Exception as e:
            logger.error(f"[BATCH_EMBEDDING] Error in one-time processing: {e}", exc_info=True)
            raise  # Re-raise exception so caller can handle it

    @classmethod
    async def close_pool(cls):
        """Stub - pool is closed globally"""
        pass

    async def close(self):
        """Stub - pool is closed globally"""
        pass