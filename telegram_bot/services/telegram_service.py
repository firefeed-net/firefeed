# telegram_bot/services/telegram_service.py - Telegram messaging service
import asyncio
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from telegram.error import RetryAfter, BadRequest

from telegram_bot.models.rss_item import PreparedRSSItem
from telegram_bot.services.user_state_service import user_manager
from telegram_bot.services.api_service import get_categories
from telegram_bot.utils.validation_utils import validate_image_url
from telegram_bot.utils.formatting_utils import (
    format_personal_rss_message, format_channel_rss_message,
    create_lang_note, create_hashtags, truncate_caption
)
from services.translation.translations import TRANSLATED_FROM_LABELS, READ_MORE_LABELS
from telegram_bot.config import CHANNEL_IDS, CHANNEL_CATEGORIES
from config import RSS_PARSER_MEDIA_TYPE_PRIORITY
from utils.text import TextProcessor

logger = logging.getLogger(__name__)

# Global semaphores for rate limiting
SEND_SEMAPHORE = asyncio.Semaphore(5)
RSS_ITEM_PROCESSING_SEMAPHORE = asyncio.Semaphore(10)


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=30))
async def send_personal_rss_items(bot, prepared_rss_item: PreparedRSSItem, subscribers_cache=None):
    """Sends personal RSS items to subscribers."""
    news_id = prepared_rss_item.original_data.get("id")
    logger.info(f"Sending personal RSS item: {prepared_rss_item.original_data['title'][:50]}...")
    category = prepared_rss_item.original_data.get("category")
    if not category:
        logger.warning(f"RSS item {news_id} has no category")
        return

    # Use subscribers cache if provided
    if subscribers_cache is not None:
        subscribers = subscribers_cache.get(category, [])
    else:
        # Fallback to old method if cache not provided
        subscribers = await user_manager.get_subscribers_for_category(category)

    if not subscribers:
        logger.debug(f"No subscribers for category {category}")
        return

    translations_cache = prepared_rss_item.translations
    original_rss_item_lang = prepared_rss_item.original_data.get("lang", "")

    for i, user in enumerate(subscribers):
        try:
            user_id = user["id"]
            user_lang = user.get("language_code", "en")

            # Check if item has content in user's language
            title_to_send = None
            content_to_send = None

            # If user's language matches item's original language
            if user_lang == original_rss_item_lang:
                title_to_send = prepared_rss_item.original_data["title"]
                content_to_send = prepared_rss_item.original_data.get("content", "")
            # Otherwise, look for translation in user's language
            elif user_lang in translations_cache and translations_cache[user_lang]:
                translation_data = translations_cache[user_lang]
                title_to_send = translation_data.get("title", "")
                content_to_send = translation_data.get("content", "")

            # If no suitable content, skip user
            if not title_to_send or not title_to_send.strip():
                logger.debug(f"Skipping user {user_id} - no content in language {user_lang}")
                continue

            title_to_send = TextProcessor.clean(title_to_send)
            content_to_send = TextProcessor.clean(content_to_send)

            lang_note = ""
            if user_lang != original_rss_item_lang:
                lang_note = (
                    f"\n🌐 {TRANSLATED_FROM_LABELS.get(user_lang, 'Translated from')} {original_rss_item_lang.upper()}\n"
                )

            source_url = prepared_rss_item.original_data.get("link", "")
            content_text = format_personal_rss_message(
                title_to_send, content_to_send,
                prepared_rss_item.original_data.get("source", "Unknown Source"),
                category, lang_note, user_lang, source_url
            )

            # Determine media based on priority
            priority = RSS_PARSER_MEDIA_TYPE_PRIORITY.lower()
            media_filename = None
            media_type = None

            if priority == "image":
                if prepared_rss_item.image_filename:
                    media_filename = prepared_rss_item.image_filename
                    media_type = "image"
                elif prepared_rss_item.video_filename:
                    media_filename = prepared_rss_item.video_filename
                    media_type = "video"
            elif priority == "video":
                if prepared_rss_item.video_filename:
                    media_filename = prepared_rss_item.video_filename
                    media_type = "video"
                elif prepared_rss_item.image_filename:
                    media_filename = prepared_rss_item.image_filename
                    media_type = "image"

            logger.debug(f"send_personal_rss_items media_filename = {media_filename}, media_type = {media_type}")

            if media_filename and media_type == "image":
                # Check image availability and correctness
                if await validate_image_url(media_filename):
                    logger.debug(f"Image passed validation: {media_filename}")
                else:
                    logger.warning(f"Image failed validation, sending without it: {media_filename}")
                    media_filename = None  # Reset media
                    continue  # Continue without media
            elif media_filename and media_type == "video":
                # For video, we assume it's already validated during processing
                logger.debug(f"Using video: {media_filename}")

            if media_filename:
                caption = truncate_caption(content_text)
                try:
                    if media_type == "image":
                        await bot.send_photo(chat_id=user_id, photo=media_filename, caption=caption, parse_mode="HTML")
                    elif media_type == "video":
                        await bot.send_video(chat_id=user_id, video=media_filename, caption=caption, parse_mode="HTML")
                except RetryAfter as e:
                    logger.warning(f"Flood control for user {user_id}, waiting {e.retry_after} seconds")
                    await asyncio.sleep(e.retry_after + 1)
                    if media_type == "image":
                        await bot.send_photo(chat_id=user_id, photo=media_filename, caption=caption, parse_mode="HTML")
                    elif media_type == "video":
                        await bot.send_video(chat_id=user_id, video=media_filename, caption=caption, parse_mode="HTML")
                except BadRequest as e:
                    if "Wrong type of the web page content" in str(e):
                        logger.warning(f"Incorrect content type for user {user_id}, sending without media: {media_filename}")
                        # Send without media
                        try:
                            await bot.send_message(
                                chat_id=user_id, text=caption, parse_mode="HTML", disable_web_page_preview=True
                            )
                        except Exception as send_error:
                            logger.error(f"Error sending message to user {user_id}: {send_error}")
                    else:
                        logger.error(f"BadRequest when sending media to user {user_id}: {e}")
                except Exception as e:
                    logger.error(f"Error sending media to user {user_id}: {e}")
            else:
                try:
                    await bot.send_message(
                        chat_id=user_id, text=content_text, parse_mode="HTML", disable_web_page_preview=True
                    )
                except RetryAfter as e:
                    logger.warning(f"Flood control for user {user_id}, waiting {e.retry_after} seconds")
                    await asyncio.sleep(e.retry_after + 1)
                    await bot.send_message(
                        chat_id=user_id, text=content_text, parse_mode="HTML", disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")

            if i < len(subscribers) - 1:
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error sending personal RSS item to user {user.get('id', 'Unknown ID')}: {e}")


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=30))
async def post_to_channel(bot, prepared_rss_item: PreparedRSSItem):
    """Publishes RSS item to Telegram channels."""
    original_title = prepared_rss_item.original_data["title"]
    news_id = prepared_rss_item.original_data.get("id")
    feed_id = prepared_rss_item.feed_id

    # Get or create feed lock
    from telegram_bot.services.rss_service import FEED_LOCKS
    if feed_id not in FEED_LOCKS:
        FEED_LOCKS[feed_id] = asyncio.Lock()
    feed_lock = FEED_LOCKS[feed_id]

    async with feed_lock:
        logger.info(f"Publishing RSS item to channels: {original_title[:50]}...")

        # Check Telegram publication limits
        from telegram_bot.services.database_service import get_feed_cooldown_and_max_news, get_recent_telegram_publications_count
        cooldown_minutes, max_news_per_hour = await get_feed_cooldown_and_max_news(feed_id)
        recent_telegram_count = await get_recent_telegram_publications_count(feed_id, cooldown_minutes)

        if recent_telegram_count >= max_news_per_hour:
            logger.info(f"[SKIP] Feed {feed_id} reached Telegram publication limit {max_news_per_hour} in {cooldown_minutes} minutes. Published: {recent_telegram_count}")
            return

        # Check time-based limit
        from telegram_bot.services.database_service import get_last_telegram_publication_time
        from datetime import datetime, timezone, timedelta
        last_telegram_time = await get_last_telegram_publication_time(feed_id)
        if last_telegram_time:
            elapsed = datetime.now(timezone.utc) - last_telegram_time
            min_interval = timedelta(minutes=60 / max_news_per_hour)
            cooldown_limit = timedelta(minutes=cooldown_minutes)
            effective_limit = min(min_interval, cooldown_limit)
            if elapsed < effective_limit:
                remaining_time = effective_limit - elapsed
                logger.info(f"[SKIP] Feed {feed_id} on Telegram cooldown. Remaining: {remaining_time}")
                return

        logger.debug(f"post_to_channel prepared_rss_item = {prepared_rss_item}")
        original_content = prepared_rss_item.original_data.get("content", "")
        category = prepared_rss_item.original_data.get("category", "")
        original_source = prepared_rss_item.original_data.get("source", "UnknownSource")
        original_lang = prepared_rss_item.original_data["lang"]
        translations_cache = prepared_rss_item.translations
        channels_list = list(CHANNEL_IDS.items())

        # Send to channels where translation or original exists
        for target_lang, channel_id in channels_list:
            try:
                # Determine whether to use translation or original
                if target_lang == original_lang:
                    # Original language
                    title = TextProcessor.clean(original_title)
                    content = TextProcessor.clean(original_content)
                    lang_note = ""
                    translation_id = None  # No translation for original language
                elif target_lang in translations_cache and translations_cache[target_lang]:
                    # There is translation
                    translation_data = translations_cache[target_lang]
                    title = TextProcessor.clean(translation_data.get("title", original_title))
                    content = TextProcessor.clean(translation_data.get("content", original_content))
                    lang_note = create_lang_note(target_lang, original_lang)
                    # Получаем ID перевода для отслеживания публикации
                    from telegram_bot.services.database_service import get_translation_id
                    translation_id = await get_translation_id(news_id, target_lang)
                    if not translation_id:
                        logger.warning(f"Translation ID not found for {news_id} in {target_lang}, skipping publication")
                        continue
                else:
                    # No translation, skip
                    logger.debug(f"No translation for {news_id} in {target_lang}, skipping publication")
                    continue

                hashtags = create_hashtags(category, original_source)
                source_url = prepared_rss_item.original_data.get("link", "")
                content_text = format_channel_rss_message(title, content, lang_note, hashtags, source_url)

                # Determine media based on priority
                priority = RSS_PARSER_MEDIA_TYPE_PRIORITY.lower()
                media_filename = None
                media_type = None

                if priority == "image":
                    if prepared_rss_item.image_filename:
                        media_filename = prepared_rss_item.image_filename
                        media_type = "image"
                    elif prepared_rss_item.video_filename:
                        media_filename = prepared_rss_item.video_filename
                        media_type = "video"
                elif priority == "video":
                    if prepared_rss_item.video_filename:
                        media_filename = prepared_rss_item.video_filename
                        media_type = "video"
                    elif prepared_rss_item.image_filename:
                        media_filename = prepared_rss_item.image_filename
                        media_type = "image"

                logger.debug(f"post_to_channel media_filename = {media_filename}, media_type = {media_type}")

                if media_filename and ((media_type == "image" and await validate_image_url(media_filename)) or media_type == "video"):
                    # Media passed validation - send with appropriate method
                    logger.debug(f"Media passed validation: {media_filename}")

                    caption = truncate_caption(content_text)
                    try:
                        if media_type == "image":
                            message = await bot.send_photo(
                                chat_id=channel_id, photo=media_filename, caption=caption, parse_mode="HTML"
                            )
                        elif media_type == "video":
                            message = await bot.send_video(
                                chat_id=channel_id, video=media_filename, caption=caption, parse_mode="HTML"
                            )
                        message_id = message.message_id
                    except RetryAfter as e:
                        logger.warning(f"Flood control for channel {channel_id}, waiting {e.retry_after} seconds")
                        await asyncio.sleep(e.retry_after + 1)
                        if media_type == "image":
                            message = await bot.send_photo(
                                chat_id=channel_id, photo=media_filename, caption=caption, parse_mode="HTML"
                            )
                        elif media_type == "video":
                            message = await bot.send_video(
                                chat_id=channel_id, video=media_filename, caption=caption, parse_mode="HTML"
                            )
                        message_id = message.message_id
                    except BadRequest as e:
                        if "Wrong type of the web page content" in str(e):
                            logger.warning(f"Incorrect content type for channel {channel_id}, sending without media: {media_filename}")
                            # Send without media
                            try:
                                message = await bot.send_message(
                                    chat_id=channel_id, text=content_text, parse_mode="HTML", disable_web_page_preview=True
                                )
                                message_id = message.message_id
                            except Exception as send_error:
                                logger.error(f"Error sending message to channel {channel_id}: {send_error}")
                                continue
                        else:
                            logger.error(f"BadRequest when sending media to channel {channel_id}: {e}")
                            continue
                    except Exception as e:
                        logger.error(f"Error sending media to channel {channel_id}: {e}")
                        continue
                else:
                    # No media or it failed validation - send text only
                    if media_filename:
                        logger.warning(f"Media failed validation, sending without it: {media_filename}")
                    try:
                        message = await bot.send_message(
                            chat_id=channel_id, text=content_text, parse_mode="HTML", disable_web_page_preview=True
                        )
                        message_id = message.message_id
                    except RetryAfter as e:
                        logger.warning(f"Flood control for channel {channel_id}, waiting {e.retry_after} seconds")
                        await asyncio.sleep(e.retry_after + 1)
                        message = await bot.send_message(
                            chat_id=channel_id, text=content_text, parse_mode="HTML", disable_web_page_preview=True
                        )
                        message_id = message.message_id
                    except Exception as e:
                        logger.error(f"Error sending message to channel {channel_id}: {e}")
                        continue

                # Mark publication in DB
                if translation_id:
                    # This is a translation
                    from telegram_bot.services.database_service import mark_translation_as_published
                    await mark_translation_as_published(translation_id, channel_id, message_id)
                else:
                    # This is original news
                    from telegram_bot.services.database_service import mark_original_as_published
                    await mark_original_as_published(news_id, channel_id, message_id)

                logger.info(f"Published to {channel_id}: {title[:50]}...")

                # Add 5 second delay between publications to different channels
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error sending to {channel_id}: {e}")

        # Add delay after publication to enforce time-based limits
        if max_news_per_hour > 0:
            delay_seconds = 60 / max_news_per_hour
            logger.info(f"Adding {delay_seconds} seconds delay after publication for feed {feed_id}")
            await asyncio.sleep(delay_seconds)