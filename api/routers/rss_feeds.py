import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from api.middleware import limiter
from api import database, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users/me/rss-feeds", tags=["user_rss_feeds"])


async def get_current_user():
    raise HTTPException(status_code=501, detail="Not implemented dependency")


@router.post("/", response_model=models.UserRSSFeedResponse, status_code=201)
@limiter.limit("300/minute")
async def create_user_rss_feed(feed: models.UserRSSFeedCreate, current_user: dict = Depends(get_current_user)):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")

    new_feed = await database.create_user_rss_feed(
        pool, current_user["id"], feed.url, feed.name, feed.category_id, feed.language
    )
    if not new_feed:
        raise HTTPException(status_code=500, detail="Failed to create RSS feed")
    return models.UserRSSFeedResponse(**new_feed)


@router.get("/", response_model=models.PaginatedResponse[models.UserRSSFeedResponse])
@limiter.limit("300/minute")
async def get_user_rss_feeds(
    limit: int = Query(50, le=100, gt=0),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")
    feeds = await database.get_user_rss_feeds(pool, current_user["id"], limit, offset)
    feed_models = [models.UserRSSFeedResponse(**feed) for feed in feeds]
    return models.PaginatedResponse[models.UserRSSFeedResponse](count=len(feed_models), results=feed_models)


@router.get("/{feed_id}", response_model=models.UserRSSFeedResponse)
@limiter.limit("300/minute")
async def get_user_rss_feed(feed_id: int, current_user: dict = Depends(get_current_user)):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")
    feed = await database.get_user_rss_feed_by_id(pool, current_user["id"], feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="RSS feed not found")
    return models.UserRSSFeedResponse(**feed)


@router.put("/{feed_id}", response_model=models.UserRSSFeedResponse)
@limiter.limit("300/minute")
async def update_user_rss_feed(feed_id: int, feed_update: models.UserRSSFeedUpdate, current_user: dict = Depends(get_current_user)):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")
    update_data = {}
    if feed_update.name is not None:
        update_data["name"] = feed_update.name
    if feed_update.category_id is not None:
        update_data["category_id"] = feed_update.category_id
    if feed_update.is_active is not None:
        update_data["is_active"] = feed_update.is_active
    updated_feed = await database.update_user_rss_feed(pool, current_user["id"], feed_id, update_data)
    if not updated_feed:
        raise HTTPException(status_code=404, detail="RSS feed not found or failed to update")
    return models.UserRSSFeedResponse(**updated_feed)


@router.delete("/{feed_id}", status_code=204)
@limiter.limit("300/minute")
async def delete_user_rss_feed(feed_id: int, current_user: dict = Depends(get_current_user)):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")
    success = await database.delete_user_rss_feed(pool, current_user["id"], feed_id)
    if not success:
        raise HTTPException(status_code=404, detail="RSS feed not found")
    return
