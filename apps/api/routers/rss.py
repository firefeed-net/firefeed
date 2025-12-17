import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from feedgen.feed import FeedGenerator
from email.utils import formatdate

from di_container import get_service
from interfaces import ICategoryRepository, ISourceRepository, IRSSItemRepository
from exceptions import RSSException, CacheException
# Config will be accessed via DI
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Redis client for caching - now from DI
import redis

def get_redis_client():
    return get_service(redis.Redis)

CACHE_TTL_SECONDS = 3600  # 1 hour

router = APIRouter(
    tags=["rss"],
    responses={
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)


def generate_rss_feed(results, columns, language, feed_title, feed_description):
    """Helper function to generate RSS feed from results."""
    fg = FeedGenerator()
    fg.title(feed_title)
    fg.description(feed_description)
    fg.link(href="https://firefeed.net", rel="alternate")
    fg.language(language)

    for row in results:
        row_dict = dict(zip(columns, row))

        # Determine title and content based on language
        if language == row_dict["original_language"]:
            title = row_dict["original_title"]
            content = row_dict["original_content"]
        else:
            # Use translation if available
            trans_key = f"title_{language}"
            title = row_dict.get(trans_key) or row_dict["original_title"]
            cont_key = f"content_{language}"
            content = row_dict.get(cont_key) or row_dict["original_content"]

        # Skip if no title or content
        if not title or not content:
            continue

        fe = fg.add_entry()
        fe.title(title)
        fe.description(content)
        fe.link(href=row_dict["source_url"] or "https://firefeed.net")
        if row_dict["created_at"]:
            fe.pubDate(formatdate(row_dict["created_at"].timestamp(), localtime=False))

        # Add image as enclosure if available
        if row_dict["image_filename"]:
            image_url = f"https://firefeed.net/data/images/{row_dict['image_filename']}"
            fe.enclosure(url=image_url, type="image/jpeg")  # Assuming JPEG, but could be dynamic

    return fg.rss_str(pretty=True)


@router.get(
    "/api/v1/rss/{language}/category/{category_name}",
    summary="Get RSS feed for a specific category in a given language",
    description="""
    Retrieve an RSS feed containing news articles for the specified category, translated to the requested language.

    **Path parameters:**
    - `language`: Language code (en, ru, de, fr)
    - `category_name`: Category name (e.g., Technology, Politics)

    **Rate limit:** 100 requests per minute
    """,
    responses={
        200: {
            "description": "RSS feed XML",
            "content": {"application/rss+xml": {}}
        },
        404: {"description": "Category not found"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_rss_feed_by_category(language: str, category_name: str):
    config_obj = get_service(dict)
    supported_languages = config_obj.get('SUPPORTED_LANGUAGES', ['en', 'ru', 'de', 'fr'])
    if language not in supported_languages:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    cache_key = f"rss:category:{category_name}:{language}"

    # Try to get from cache
    cached_rss = get_redis_client().get(cache_key)
    if cached_rss:
        return Response(content=cached_rss, media_type="application/rss+xml")

    category_repo = get_service(ICategoryRepository)
    rss_item_repo = get_service(IRSSItemRepository)

    try:
        # Get category ID by name
        category_id = await category_repo.get_category_id_by_name(category_name)
        if category_id is None:
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

        # Get RSS items for the category (last hour, max 10 items)
        from_date = datetime.now(timezone.utc) - timedelta(hours=1)
        total_count, results, columns = await rss_item_repo.get_all_rss_items_list(
            limit=10,  # Max 10 items per hour
            offset=0,
            category_name=category_name,
            from_date=from_date
        )

        feed_title = f"FireFeed - {category_name} ({language.upper()})"
        feed_description = f"Latest news in {category_name} category, translated to {language.upper()}"
        rss_xml = generate_rss_feed(results, columns, language, feed_title, feed_description)

        # Cache the result
        get_redis_client().setex(cache_key, CACHE_TTL_SECONDS, rss_xml)

        return Response(content=rss_xml, media_type="application/rss+xml")

    except HTTPException:
        raise
    except RSSException as e:
        logger.error(f"[API] RSS error generating feed for category: {e}")
        raise HTTPException(status_code=400, detail=f"RSS processing error: {str(e)}")
    except CacheException as e:
        logger.error(f"[API] Cache error generating feed for category: {e}")
        raise HTTPException(status_code=500, detail="Cache error")
    except Exception as e:
        logger.error(f"[API] Error generating RSS feed for category: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/api/v1/rss/{language}/source/{source_alias}",
    summary="Get RSS feed for a specific source in a given language",
    description="""
    Retrieve an RSS feed containing news articles from the specified source, translated to the requested language.

    **Path parameters:**
    - `language`: Language code (en, ru, de, fr)
    - `source_alias`: Source alias (e.g., bbc, cnn)

    **Rate limit:** 100 requests per minute
    """,
    responses={
        200: {
            "description": "RSS feed XML",
            "content": {"application/rss+xml": {}}
        },
        404: {"description": "Source not found"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_rss_feed_by_source(language: str, source_alias: str):
    config_obj = get_service(dict)
    supported_languages = config_obj.get('SUPPORTED_LANGUAGES', ['en', 'ru', 'de', 'fr'])
    if language not in supported_languages:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    cache_key = f"rss:source:{source_alias}:{language}"

    # Try to get from cache
    cached_rss = get_redis_client().get(cache_key)
    if cached_rss:
        return Response(content=cached_rss, media_type="application/rss+xml")

    source_repo = get_service(ISourceRepository)
    rss_item_repo = get_service(IRSSItemRepository)

    try:
        # Get source ID by alias
        source_id = await source_repo.get_source_id_by_alias(source_alias)
        if source_id is None:
            raise HTTPException(status_code=404, detail=f"Source '{source_alias}' not found")

        # Get RSS items for the source (last hour, max 10 items)
        from_date = datetime.now(timezone.utc) - timedelta(hours=1)
        total_count, results, columns = await rss_item_repo.get_all_rss_items_list(
            limit=10,  # Max 10 items per hour
            offset=0,
            source_alias=source_alias,
            from_date=from_date
        )

        feed_title = f"FireFeed - {source_alias} ({language.upper()})"
        feed_description = f"Latest news from {source_alias} source, translated to {language.upper()}"
        rss_xml = generate_rss_feed(results, columns, language, feed_title, feed_description)

        # Cache the result
        get_redis_client().setex(cache_key, CACHE_TTL_SECONDS, rss_xml)

        return Response(content=rss_xml, media_type="application/rss+xml")

    except HTTPException:
        raise
    except RSSException as e:
        logger.error(f"[API] RSS error generating feed for source: {e}")
        raise HTTPException(status_code=400, detail=f"RSS processing error: {str(e)}")
    except CacheException as e:
        logger.error(f"[API] Cache error generating feed for source: {e}")
        raise HTTPException(status_code=500, detail="Cache error")
    except Exception as e:
        logger.error(f"[API] Error generating RSS feed for source: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")