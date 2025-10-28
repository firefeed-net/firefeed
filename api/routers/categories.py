import logging
from typing import Optional, List, Set
from fastapi import APIRouter, Depends, HTTPException, Query

from api.middleware import limiter
from api import database, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users/me/categories", tags=["user_categories"])


async def get_current_user():
    raise HTTPException(status_code=501, detail="Not implemented dependency")


@router.get("/", response_model=models.UserCategoriesResponse)
@limiter.limit("300/minute")
async def get_user_categories(
    current_user: dict = Depends(get_current_user),
    source_ids: Optional[List[int]] = Query(None),
):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")

    categories = await database.get_user_categories(pool, current_user["id"], source_ids)
    return models.UserCategoriesResponse(category_ids=[cat["id"] for cat in categories])


@router.put("/", response_model=models.SuccessResponse)
@limiter.limit("300/minute")
async def update_user_categories(
    category_update: models.UserCategoriesUpdate, current_user: dict = Depends(get_current_user)
):
    category_ids: Set[int] = category_update.category_ids
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")

    existing_categories = await database.get_all_category_ids(pool)
    invalid_ids = category_ids - existing_categories
    if invalid_ids:
        raise HTTPException(status_code=400, detail=f"Invalid category IDs: {list(invalid_ids)}")

    success = await database.update_user_categories(pool, current_user["id"], category_ids)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user categories")

    return models.SuccessResponse(message="User categories successfully updated")
