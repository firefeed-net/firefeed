import logging
from fastapi import APIRouter, Depends, HTTPException

from api.middleware import limiter
from api import database, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


async def get_current_user(token: str = Depends()):
    # Placeholder; in a full refactor we would move auth dependency here.
    raise HTTPException(status_code=501, detail="Not implemented dependency")


@router.get("/me", response_model=models.UserResponse)
@limiter.limit("300/minute")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return models.UserResponse(**current_user)


@router.put("/me", response_model=models.UserResponse)
@limiter.limit("300/minute")
async def update_current_user(user_update: models.UserUpdate, current_user: dict = Depends(get_current_user)):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")

    if user_update.email and user_update.email != current_user["email"]:
        existing_user = await database.get_user_by_email(pool, user_update.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    update_data = {}
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.language is not None:
        update_data["language"] = user_update.language

    updated_user = await database.update_user(pool, current_user["id"], update_data)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to update user")
    return models.UserResponse(**updated_user)


@router.delete("/me", status_code=204)
@limiter.limit("300/minute")
async def delete_current_user(current_user: dict = Depends(get_current_user)):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")
    success = await database.delete_user(pool, current_user["id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    return
