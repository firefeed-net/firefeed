import logging
from typing import Optional, List, Set
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.api.middleware import limiter
from apps.api import models
from di_container import get_service
from interfaces import ICategoryRepository
from apps.api.deps import get_current_user
from exceptions import DatabaseException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/users/me/categories",
    tags=["user_categories"],
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)




@router.get(
    "/",
    response_model=models.UserCategoriesResponse,
    summary="Get user's subscribed categories",
    description="""
    Retrieve the list of news categories the authenticated user is subscribed to.

    Returns category IDs that the user has selected for personalized news feeds.
    Results can be filtered by associated source IDs.

    **Query parameters:**
    - `source_ids`: Filter categories by associated news sources (multiple values allowed)

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "User's subscribed categories",
            "model": models.UserCategoriesResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def get_user_categories(
    request: Request,
    current_user: dict = Depends(get_current_user),
    source_ids: Optional[List[int]] = Query(None, description="Filter by associated source IDs"),
):
    category_repo = get_service(ICategoryRepository)
    try:
        categories = await category_repo.get_user_categories(current_user["id"], source_ids)
        return models.UserCategoriesResponse(category_ids=[cat["id"] for cat in categories])
    except DatabaseException as e:
        logger.error(f"Database error in get_user_categories: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.put(
    "/",
    response_model=models.SuccessResponse,
    summary="Update user's category subscriptions",
    description="""
    Update the list of news categories the authenticated user is subscribed to.

    This replaces all existing category subscriptions with the provided list.
    Categories determine which news articles appear in the user's personalized feeds.

    **Validation:**
    - All provided category IDs must exist in the system
    - Invalid category IDs will result in a 400 error

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Categories updated successfully",
            "model": models.SuccessResponse
        },
        400: {
            "description": "Bad Request - Invalid category IDs provided",
            "model": models.HTTPError
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def update_user_categories(
    request: Request,
    category_update: models.UserCategoriesUpdate, current_user: dict = Depends(get_current_user)
):
    category_ids: Set[int] = category_update.category_ids
    category_repo = get_service(ICategoryRepository)

    try:
        existing_categories = await category_repo.get_all_category_ids()
        invalid_ids = category_ids - set(existing_categories)
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Invalid category IDs: {list(invalid_ids)}")

        success = await category_repo.update_user_categories(current_user["id"], list(category_ids))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update user categories")

        return models.SuccessResponse(message="User categories successfully updated")
    except DatabaseException as e:
        logger.error(f"Database error in update_user_categories: {e}")
        raise HTTPException(status_code=500, detail="Database error")
