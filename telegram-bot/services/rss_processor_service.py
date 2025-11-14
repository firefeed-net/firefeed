import asyncio
import logging
from typing import Dict, Optional

from telegram.ext import ContextTypes

from ..interfaces.rss_processor_interface import IRSSProcessorService
from ..interfaces.bot_interface import IBotService
from ..interfaces.database_interface import IDatabaseService
from ..interfaces.api_client_interface import IAPIClientService
from ..interfaces.image_validator_interface import IImageValidatorService
from ..models.prepared_rss_item import PreparedRSSItem
from ..utils.text_processor import TextProcessor

logger = logging.getLogger(__name__)


class RSSProcessorService(IRSSProcessorService):
    """Service for processing RSS items."""

    def __init__(self, bot_service: IBotService, database_service: IDatabaseService,
                 api_client_service: IAPIClientService, image_validator_service: IImageValidatorService,
                 send_semaphore: asyncio.Semaphore, rss_item_processing_semaphore: asyncio.Semaphore,
                 channel_categories: Dict[str, bool]):
        self.bot_service = bot_service
        self.database_service = database_service
        self.api_client_service = api_client_service
        self.image_validator_service = image_validator_service
        self.send_semaphore = send_semaphore
        self.rss_item_processing_semaphore = rss_item_processing_semaphore
        self.channel_categories = channel_categories

    async def process_rss_item(self, context, rss_item_from_api, subscribers_cache=None, channel_categories_cache=None) -> bool:
        """Processes RSS item received from API."""
        async with self.rss_item_processing_semaphore:
            news_id = rss_item_from_api.get("news_id")  # ID remains news_id for compatibility
            logger.debug(f"Starting processing of RSS item {news_id} from API")

            # Convert API data to format expected by the rest of the code
            original_data = {
                "id": rss_item_from_api.get("news_id"),
                "title": rss_item_from_api.get("original_title"),
                "content": rss_item_from_api.get("original_content"),
                "category": rss_item_from_api.get("category"),
                "source": rss_item_from_api.get("source"),
                "lang": rss_item_from_api.get("original_language"),
                "link": rss_item_from_api.get("source_url"),
                "image_url": rss_item_from_api.get("image_url"),
            }

            logger.debug(f"original_data = {original_data}")

            # Translation processing
            translations = {}
            if rss_item_from_api.get("translations"):
                for lang, translation_data in rss_item_from_api["translations"].items():
                    translations[lang] = {
                        "title": translation_data.get("title", ""),
                        "content": translation_data.get("content", ""),
                        "category": translation_data.get("category", ""),
                    }

            logger.debug(f"Preparation of RSS item {news_id} completed.")

            prepared_rss_item = PreparedRSSItem(
                original_data=original_data,
                translations=translations,
                image_filename=original_data.get("image_url"),  # because that's how API returns
                feed_id=rss_item_from_api.get("feed_id"),
            )

            async def limited_post_to_channel():
                async with self.send_semaphore:
                    await self.bot_service.post_to_channel(prepared_rss_item)

            async def limited_send_personal_rss_items():
                async with self.send_semaphore:
                    await self.bot_service.send_personal_rss_items(prepared_rss_item, subscribers_cache)

            tasks_to_await = []
            category = rss_item_from_api.get("category")
            # Use cache to check category suitability for general channel
            if category and channel_categories_cache and channel_categories_cache.get(category, False):
                tasks_to_await.append(limited_post_to_channel())

            # Check if there are subscribers for category before adding personal send task
            if category and subscribers_cache and subscribers_cache.get(category):
                tasks_to_await.append(limited_send_personal_rss_items())
            else:
                logger.debug(f"Skipping personal send for news {news_id} - no subscribers for category {category}")

            if tasks_to_await:
                await asyncio.gather(*tasks_to_await, return_exceptions=True)

            # Mark RSS item as published in Telegram
            # For channels, publication is already marked in post_to_channel
            # For personal sends, no need to mark publication in DB
            pass

            logger.debug(f"Completion of RSS item {news_id} processing")
            return True

    async def monitor_rss_items_task(self, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Starting RSS items monitoring task")
        try:
            # Get unprocessed RSS items via API
            rss_response = await self.api_client_service.get_rss_items_list(limit=20, telegram_published="false", include_all_translations="true")
            if not isinstance(rss_response, dict):
                logger.error(f"Invalid API response format: {type(rss_response)}")
                return

            unprocessed_rss_list = rss_response.get("results", [])
            logger.info(f"Received {len(unprocessed_rss_list)} RSS items from API")

            if not unprocessed_rss_list:
                logger.info("No RSS items to process.")
                return

            # Collect unique categories to optimize subscriber queries
            unique_categories = set()
            for rss_item in unprocessed_rss_list:
                category = rss_item.get("category")
                if category:
                    unique_categories.add(category)

            # Preliminary fetching of subscribers for unique categories
            subscribers_cache = {}
            # Cache for checking categories suitability for general channel
            channel_categories_cache = {}
            for category in unique_categories:
                subscribers = await self.bot_service.user_manager_service.get_subscribers_for_category(category)
                subscribers_cache[category] = subscribers
                channel_categories_cache[category] = category in self.channel_categories
                if not subscribers:
                    logger.info(f"No subscribers for category {category}")
                if channel_categories_cache[category]:
                    logger.info(f"Category '{category}' is suitable for general channel")
                else:
                    logger.info(f"Category '{category}' is NOT suitable for general channel")

            processing_tasks = [self.process_rss_item(context, rss_item, subscribers_cache, channel_categories_cache) for rss_item in unprocessed_rss_list]

            logger.info(f"Starting processing of {len(processing_tasks)} RSS items...")
            try:
                await asyncio.gather(*processing_tasks, return_exceptions=True)
                logger.info("All RSS items from current batch processed.")
            except Exception as e:
                logger.error(f"Error processing batch of RSS items: {e}")

        except asyncio.TimeoutError:
            logger.error("Timeout getting RSS items")
        except Exception as e:
            logger.error(f"Error in monitoring task: {e}")