# telegram_bot/services/rss_service.py - RSS processing service
import asyncio
import logging
from typing import Dict, Any, Optional
from collections import defaultdict

from ..models.rss_item import PreparedRSSItem
from ..services.api_service import get_rss_items_list
from ..services import user_state_service
from ..services.telegram_service import send_personal_rss_items, post_to_channel, SEND_SEMAPHORE
from di_container import get_service

logger = logging.getLogger(__name__)

# Global feed locks for concurrent processing control
FEED_LOCKS: Dict[int, asyncio.Lock] = {}


async def process_rss_item(context, rss_item_from_api, subscribers_cache=None, channel_categories_cache=None):
    """Processes RSS item received from API."""
    async with asyncio.Semaphore(10):  # RSS_ITEM_PROCESSING_SEMAPHORE equivalent
        news_id = rss_item_from_api.get("news_id")  # ID remains news_id for compatibility
        logger.debug(f"Starting processing of RSS item {news_id} from API")

        # Convert API data to format expected by the rest of the code
        original_data = {
            "id": rss_item_from_api.get("news_id"),
            "title": rss_item_from_api.get("original_title"),
            "content": rss_item_from_api.get("original_content"),
            "category": rss_item_from_api.get("category"),
            "source": rss_item_from_api.get("source_name"),
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
            video_filename=rss_item_from_api.get("video_filename"),
            feed_id=rss_item_from_api.get("feed_id"),
        )

        async def limited_post_to_channel():
            async with SEND_SEMAPHORE:
                await post_to_channel(context.bot, prepared_rss_item)

        async def limited_send_personal_rss_items():
            async with SEND_SEMAPHORE:
                await send_personal_rss_items(context.bot, prepared_rss_item, subscribers_cache)

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


async def monitor_rss_items_task(context):
    """Monitor RSS items and process new ones."""
    logger.info("Starting RSS items monitoring task")

    try:
        # Get RSS items not published to users via API
        rss_response = await get_rss_items_list(limit=20, telegram_users_published="false")
        if not isinstance(rss_response, dict):
            logger.error(f"Invalid API response format: {type(rss_response)}")
            return

        unprocessed_rss_list = rss_response.get("results", [])
        logger.info(f"Received {len(unprocessed_rss_list)} RSS items from API")

        if not unprocessed_rss_list:
            logger.info("No RSS items to process.")
            return

        # Group RSS items by feed_id
        items_by_feed = defaultdict(list)
        for rss_item in unprocessed_rss_list:
            feed_id = rss_item.get("feed_id") or "no_feed"
            items_by_feed[feed_id].append(rss_item)

        logger.info(f"Grouped into {len(items_by_feed)} feeds")

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

        config_obj = get_service(dict)
        channel_categories = config_obj.get('CHANNEL_CATEGORIES', [])

        if user_state_service.telegram_user_service is not None:
            for category in unique_categories:
                subscribers = await user_state_service.telegram_user_service.get_subscribers_for_category(category)
                subscribers_cache[category] = subscribers
                channel_categories_cache[category] = category in channel_categories
                if not subscribers:
                    logger.info(f"No subscribers for category {category}")
                if channel_categories_cache[category]:
                    logger.info(f"Category '{category}' is suitable for general channel")
                else:
                    logger.info(f"Category '{category}' is NOT suitable for general channel")
        else:
            # No telegram_user_service - disable personal sending
            logger.warning("telegram_user_service not available - personal RSS sending disabled")
            for category in unique_categories:
                subscribers_cache[category] = []
                channel_categories_cache[category] = category in channel_categories

        # Process feeds sequentially
        for feed_id, feed_items in items_by_feed.items():
            logger.info(f"Processing feed {feed_id} with {len(feed_items)} items")
            # Process items within feed sequentially
            for rss_item in feed_items:
                try:
                    await process_rss_item(context, rss_item, subscribers_cache, channel_categories_cache)
                except Exception as e:
                    logger.error(f"Error processing RSS item {rss_item.get('news_id')} from feed {feed_id}: {e}")

        logger.info("All RSS items from current batch processed.")

    except asyncio.TimeoutError:
        logger.error("Timeout getting RSS items")
    except Exception as e:
        logger.error(f"Error in monitoring task: {e}")