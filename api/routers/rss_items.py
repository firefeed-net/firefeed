import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request

from api.middleware import limiter
from api import database, models
from api.deps import format_datetime, get_full_image_url, build_translations_dict, validate_news_query_params
import config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["news"])


def process_rss_items_results(results, columns, display_language, original_language, include_all_translations):
    news_list = []
    for row in results:
        row_dict = dict(zip(columns, row))
        translations = build_translations_dict(row_dict)
        if display_language is not None and original_language and display_language != original_language:
            if not translations or display_language not in translations:
                continue
        if display_language is not None and original_language:
            translations[original_language] = {
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
            "source": row_dict["source_name"],
            "source_url": row_dict["source_url"],
            "published_at": format_datetime(row_dict["published_at"]),
            "translations": translations,
        }
        news_list.append(models.RSSItem(**item_data))

    return news_list


@router.get("/api/v1/rss-items/")
@limiter.limit("100/minute")
async def get_news(
    request: Request,
    display_language: Optional[str] = Query(None),
    original_language: Optional[str] = Query(None),
    category_id: Optional[List[int]] = Query(None),
    source_id: Optional[List[int]] = Query(None),
    telegram_published: Optional[bool] = Query(None),
    from_date: Optional[int] = Query(None),
    search_phrase: Optional[str] = Query(None, alias="searchPhrase"),
    include_all_translations: Optional[bool] = Query(None),
    cursor_published_at: Optional[int] = Query(None),
    cursor_news_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(50, le=100, gt=0),
    offset: Optional[int] = Query(0, ge=0),
):
    if display_language is None:
        include_all_translations = True

    from_datetime, before_published_at = validate_news_query_params(display_language, from_date, cursor_published_at)
    page_offset = 0 if (cursor_published_at is not None or cursor_news_id is not None) else offset

    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    try:
        total_count, results, columns = await database.get_all_rss_items_list(
            pool,
            display_language,
            original_language,
            category_id,
            source_id,
            telegram_published,
            from_datetime,
            search_phrase,
            include_all_translations or False,
            before_published_at,
            cursor_news_id,
            limit,
            page_offset,
        )
    except Exception as e:
        logger.error(f"[API] Ошибка при выполнении запроса в get_news: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    rss_items_list = process_rss_items_results(results, columns, display_language, original_language, include_all_translations)
    return {"count": len(rss_items_list), "results": rss_items_list}


@router.get("/api/v1/rss-items/{rss_item_id}", response_model=models.RSSItem)
@limiter.limit("300/minute")
async def get_news_by_id(rss_item_id: str):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    try:
        full_result = await database.get_rss_item_by_id_full(pool, rss_item_id)
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
            "source": row_dict["source_name"],
            "source_url": row_dict["source_url"],
            "published_at": format_datetime(row_dict["published_at"]),
            "translations": build_translations_dict(row_dict),
        }
    except Exception as e:
        logger.error(f"[API] Ошибка при выполнении запроса в get_news_by_id: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    return models.RSSItem(**item_data)


@router.get("/api/v1/categories/")
@limiter.limit("300/minute")
async def get_categories(
    limit: Optional[int] = Query(100, le=1000, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    source_ids: Optional[List[int]] = Query(None),
):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    try:
        total_count, results = await database.get_all_categories_list(pool, limit, offset, source_ids)
    except Exception as e:
        logger.error(f"[API] Ошибка при выполнении запроса в get_categories: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    return {"count": total_count, "results": results}


@router.get("/api/v1/sources/")
@limiter.limit("300/minute")
async def get_sources(
    limit: Optional[int] = Query(100, le=1000, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    category_id: Optional[List[int]] = Query(None),
):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")

    try:
        total_count, results = await database.get_all_sources_list(pool, limit, offset, category_id)
    except Exception as e:
        logger.error(f"[API] Ошибка при выполнении запроса в get_sources: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    return {"count": total_count, "results": results}


@router.get("/api/v1/languages/")
@limiter.limit("300/minute")
async def get_languages():
    return {"results": config.SUPPORTED_LANGUAGES}


@router.get("/api/v1/health")
@limiter.limit("300/minute")
async def health_check():
    try:
        pool = await database.get_db_pool()
        if pool:
            db_status = "ok"
            pool_total = pool.size
            pool_free = pool.freesize
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
