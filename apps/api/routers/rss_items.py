import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.middleware import limiter
from api import models
from di_container import get_service
from interfaces import IRSSItemRepository, ICategoryRepository, ISourceRepository, IUserRepository
from api.deps import format_datetime, get_full_image_url, build_translations_dict, validate_rss_items_query_params, sanitize_search_phrase, get_current_user_by_api_key
# Config will be accessed via DI

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["rss_items"],
    responses={
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)


def process_rss_items_results(results, columns):
    rss_items_list = []
    for row in results:
        row_dict = dict(zip(columns, row))
        translations = build_translations_dict(row_dict)
        row_original_language = row_dict["original_language"]
        # Always include original language in translations
        translations[row_original_language] = {
            "title": row_dict["original_title"],
            "content": row_dict["original_content"],
        }
        item_data = {
            "news_id": row_dict["news_id"],
            "original_title": row_dict["original_title"],
            "original_content": row_dict["original_content"],
            "original_language": row_dict["original_language"],
            "image_url": get_full_image_url(row_dict["image_filename"]),
            "category": row_dict["category_name"],
            "source": row_dict.get("source_name", "Unknown"),
            "source_alias": row_dict.get("source_alias", "unknown"),
            "source_url": row_dict["source_url"],
            "created_at": format_datetime(row_dict.get("created_at")),
            "feed_id": row_dict.get("rss_feed_id"),  # May not be present
            "translations": translations,
        }
        rss_items_list.append(models.RSSItem(**item_data))

    return rss_items_list


@router.get(
    "/api/v1/rss-items/",
    summary="Get RSS items with filtering and pagination",
    description="""
    Retrieve a filtered and paginated list of RSS items (news articles).

    This endpoint supports comprehensive filtering by language, category, source, publication status,
    date range, and full-text search. Results can be paginated using offset-based or cursor-based pagination.

    **Filtering Options:**
    - `original_language`: Filter by original article language
    - `category_id`: Filter by news categories (comma-separated values or multiple params allowed, e.g., 3,5 or category_id=3&category_id=5)
    - `source_id`: Filter by news sources (comma-separated values or multiple params allowed, e.g., 1,2 or source_id=1&source_id=2)
    - `telegram_published`: Filter by Telegram publication status (true/false) - published to channels OR users
    - `telegram_channels_published`: Filter by Telegram channels publication status (true/false)
    - `telegram_users_published`: Filter by Telegram users publication status (true/false)
    - `from_date`: Filter articles published after this timestamp (Unix timestamp)
    - `search_phrase`: Full-text search in titles and content

    **Pagination:**
    - **Offset-based:** Use `limit` and `offset` parameters
    - **Cursor-based:** Use `cursor_created_at` and `cursor_rss_item_id` for keyset pagination

    **Rate limit:** 1000 requests per minute
    """,
    responses={
        200: {
            "description": "List of RSS items",
            "content": {
                "application/json": {
                    "example": {
                        "count": 50,
                        "results": [
                            {
                                "rss_item_id": "abc123",
                                "original_title": "Breaking News",
                                "original_content": "Full article content...",
                                "original_language": "en",
                                "image_url": "https://firefeed.net/data/images/2024/01/01/abc123.jpg",
                                "category": "Technology",
                                "source": "Tech News",
                                "source_alias": "bbc",
                                "source_url": "https://technews.com/article123",
                                "created_at": "2024-01-01T12:00:00Z",
                                "translations": {
                                    "ru": {"title": "Главные новости", "content": "Полный текст статьи..."},
                                    "de": {"title": "Wichtige Nachrichten", "content": "Vollständiger Artikeltext..."}
                                }
                            }
                        ]
                    }
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("1000/minute")
async def get_rss_items(
    request: Request,
    original_language: Optional[str] = Query(None),
    category_id: Optional[List[str]] = Query(None),
    source_id: Optional[List[str]] = Query(None),
    telegram_published: Optional[bool] = Query(None),
    telegram_channels_published: Optional[bool] = Query(None),
    telegram_users_published: Optional[bool] = Query(None),
    from_date: Optional[int] = Query(None),
    search_phrase: Optional[str] = Query(None, alias="searchPhrase"),
    cursor_created_at: Optional[int] = Query(None),
    cursor_rss_item_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(50, le=100, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    current_user: dict = Depends(get_current_user_by_api_key),
):
    # Parse category_id and source_id from lists of strings (supporting comma-separated or multiple params)
    category_ids = None
    if category_id:
        try:
            ids = []
            for cid in category_id:
                if ',' in cid:
                    ids.extend(int(x.strip()) for x in cid.split(',') if x.strip())
                else:
                    ids.append(int(cid.strip()))
            category_ids = ids if ids else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category_id format")

    source_ids = None
    if source_id:
        try:
            ids = []
            for sid in source_id:
                if ',' in sid:
                    ids.extend(int(x.strip()) for x in sid.split(',') if x.strip())
                else:
                    ids.append(int(sid.strip()))
            source_ids = ids if ids else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid source_id format")

    # Sanitize search phrase
    if search_phrase:
        search_phrase = sanitize_search_phrase(search_phrase)

    # Set default from_date to 24 hours ago if not provided (to avoid scanning entire table)
    import time
    if from_date is None:
        from_date = int(time.time()) - 86400  # 24 hours in seconds
        logger.info(f"[API] RSS items: using default from_date={from_date} (24h ago)")

    logger.info(f"[API] RSS items request: original_language={original_language}, "
                f"category_id={category_id}, source_id={source_id}, from_date={from_date}, limit={limit}, offset={offset}")

    from_datetime, before_created_at = validate_rss_items_query_params(from_date, cursor_created_at)
    page_offset = 0 if (cursor_created_at is not None or cursor_rss_item_id is not None) else offset

    rss_item_repo = get_service(IRSSItemRepository)

    import time
    start_time = time.time()
    try:
        total_count, results, columns = await rss_item_repo.get_all_rss_items_list(
            limit=limit,
            offset=page_offset,
            original_language=original_language,
            category_id=category_ids,
            source_id=source_ids,
            from_date=from_datetime,
            search_phrase=search_phrase,
            before_created_at=before_created_at,
            cursor_news_id=cursor_rss_item_id,
            telegram_published=telegram_published,
            telegram_channels_published=telegram_channels_published,
            telegram_users_published=telegram_users_published
        )
        query_time = time.time() - start_time
        logger.info(f"[API] RSS items query completed in {query_time:.2f} seconds, returned {len(results)} items")
    except Exception as e:
        logger.error(f"[API] Error executing query in get_rss_items: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    rss_items_list = process_rss_items_results(results, columns)
    return {"count": len(rss_items_list), "results": rss_items_list}


@router.get(
    "/api/v1/rss-items/{rss_item_id}",
    response_model=models.RSSItem,
    summary="Get specific RSS item by ID",
    description="""
    Retrieve detailed information about a specific RSS item (news article) by its unique identifier.

    Returns the complete article data including all available translations, metadata, and media URLs.

    **Path parameters:**
    - `rss_item_id`: Unique identifier of the RSS item

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "RSS item details",
            "model": models.RSSItem
        },
        404: {
            "description": "Not Found - RSS item not found",
            "model": models.HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def get_rss_item_by_id(request: Request, rss_item_id: str, current_user: dict = Depends(get_current_user_by_api_key)):
    rss_item_repo = get_service(IRSSItemRepository)

    try:
        full_result = await rss_item_repo.get_rss_item_by_id_full(rss_item_id)
        if not full_result or not full_result[0]:
            raise HTTPException(status_code=404, detail="News item not found")
        row, columns = full_result
        row_dict = dict(zip(columns, row))
        item_data = {
            "news_id": row_dict["news_id"],
            "original_title": row_dict["original_title"],
            "original_content": row_dict["original_content"],
            "original_language": row_dict["original_language"],
            "image_url": get_full_image_url(row_dict["image_filename"]),
            "category": row_dict["category_name"],
            "source": row_dict.get("source_name", "Unknown"),
            "source_alias": row_dict.get("source_alias", "unknown"),
            "source_url": row_dict["source_url"],
            "created_at": format_datetime(row_dict.get("created_at")),
            "translations": build_translations_dict(row_dict),
        }
    except Exception as e:
        logger.error(f"[API] Error executing query in get_rss_item_by_id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    return models.RSSItem(**item_data)


@router.get(
    "/api/v1/categories/",
    summary="Get available news categories",
    description="""
    Retrieve a paginated list of available news categories.

    Categories are used to classify news articles and can be used for filtering RSS items.
    Results can be filtered by associated source IDs.

    **Query parameters:**
    - `limit`: Number of categories per page (1-1000, default: 100)
    - `offset`: Number of categories to skip (default: 0)
    - `source_ids`: Filter categories by associated news sources (comma-separated values or multiple params allowed, e.g., 1,2 or source_ids=1&source_ids=2)

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of news categories",
            "content": {
                "application/json": {
                    "example": {
                        "count": 8,
                        "results": [
                            {"id": 1, "name": "Technology"},
                            {"id": 2, "name": "Politics"},
                            {"id": 3, "name": "Sports"}
                        ]
                    }
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def get_categories(
    request: Request,
    limit: Optional[int] = Query(100, le=1000, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    source_ids: Optional[List[str]] = Query(None),
    current_user: dict = Depends(get_current_user_by_api_key),
):
    source_ids_list = None
    if source_ids:
        try:
            ids = []
            for sid in source_ids:
                if ',' in sid:
                    ids.extend(int(x.strip()) for x in sid.split(',') if x.strip())
                else:
                    ids.append(int(sid.strip()))
            source_ids_list = ids if ids else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid source_ids format")

    category_repo = get_service(ICategoryRepository)

    try:
        total_count, results = await category_repo.get_all_categories_list(limit, offset, source_ids_list)
    except Exception as e:
        logger.error(f"[API] Error executing query in get_categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"count": total_count, "results": results}


@router.get(
    "/api/v1/sources/",
    summary="Get available news sources",
    description="""
    Retrieve a paginated list of available news sources.

    Sources represent the origin of news articles and can be used for filtering RSS items.
    Results can be filtered by associated category IDs.

    **Query parameters:**
    - `limit`: Number of sources per page (1-1000, default: 100)
    - `offset`: Number of sources to skip (default: 0)
    - `category_id`: Filter sources by associated categories (comma-separated values or multiple params allowed, e.g., 1,2 or category_id=1&category_id=2)

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of news sources",
            "content": {
                "application/json": {
                    "example": {
                        "count": 25,
                        "results": [
                            {
                                "id": 1,
                                "name": "BBC News",
                                "description": "British Broadcasting Corporation",
                                "alias": "bbc",
                                "logo": "bbc-logo.png",
                                "site_url": "https://bbc.com"
                            }
                        ]
                    }
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def get_sources(
    request: Request,
    limit: Optional[int] = Query(100, le=1000, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    category_id: Optional[List[str]] = Query(None),
    current_user: dict = Depends(get_current_user_by_api_key),
):
    category_ids = None
    if category_id:
        try:
            ids = []
            for cid in category_id:
                if ',' in cid:
                    ids.extend(int(x.strip()) for x in cid.split(',') if x.strip())
                else:
                    ids.append(int(cid.strip()))
            category_ids = ids if ids else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category_id format")

    source_repo = get_service(ISourceRepository)

    try:
        total_count, results = await source_repo.get_all_sources_list(limit, offset, category_ids)
    except Exception as e:
        logger.error(f"[API] Error executing query in get_sources: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"count": total_count, "results": results}


@router.get(
    "/api/v1/languages/",
    summary="Get supported languages",
    description="""
    Retrieve the list of languages supported by the FireFeed system.

    These languages are available for content translation, user interface localization,
    and filtering RSS items by original or translated language.

    **Supported languages:**
    - `en`: English
    - `ru`: Russian (Русский)
    - `de`: German (Deutsch)
    - `fr`: French (Français)

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of supported languages",
            "content": {
                "application/json": {
                    "example": {
                        "results": ["en", "ru", "de", "fr"]
                    }
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def get_languages(request: Request, current_user: dict = Depends(get_current_user_by_api_key)):
    config_obj = get_service(dict)
    return {"results": config_obj.get('SUPPORTED_LANGUAGES', ['en', 'ru', 'de', 'fr'])}


@router.get(
    "/api/v1/health",
    summary="Health check endpoint",
    description="""
    Check the health status of the FireFeed API and its dependencies.

    This endpoint provides information about the system's operational status,
    including database connectivity and connection pool statistics.

    **Response fields:**
    - `status`: Overall system status ("ok" if healthy)
    - `database`: Database connection status ("ok" or "error")
    - `db_pool`: Database connection pool information
        - `total_connections`: Total number of connections in pool
        - `free_connections`: Number of available connections

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "System health information",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "database": "ok",
                        "db_pool": {
                            "total_connections": 20,
                            "free_connections": 15
                        }
                    }
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {
            "description": "Internal Server Error - System unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "database": "error",
                        "db_pool": {
                            "total_connections": 0,
                            "free_connections": 0
                        }
                    }
                }
            }
        }
    }
)
@limiter.limit("300/minute")
async def health_check(request: Request):
    try:
        user_repo = get_service(IUserRepository)
        pool_adapter = user_repo.db_pool
        if pool_adapter and hasattr(pool_adapter, '_pool') and pool_adapter._pool:
            db_status = "ok"
            pool_total = getattr(pool_adapter._pool, 'size', 0)
            pool_free = getattr(pool_adapter._pool, 'freesize', 0)
        else:
            db_status = "error"
            pool_total = 0
            pool_free = 0
    except Exception as e:
        db_status = "error"
        pool_total = 0
        pool_free = 0
        logger.error(f"[Healthcheck] Database connection error: {e}")
    return {
        "status": "ok",
        "database": db_status,
        "db_pool": {"total_connections": pool_total, "free_connections": pool_free},
    }
