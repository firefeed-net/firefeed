import logging
from fastapi import APIRouter, Depends, HTTPException

from api.middleware import limiter
from api import database, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users/me/telegram", tags=["telegram_link"])


async def get_current_user():
    raise HTTPException(status_code=501, detail="Not implemented dependency")


@router.post("/generate-link", response_model=models.TelegramLinkResponse)
@limiter.limit("300/minute")
async def generate_telegram_link_code(current_user: dict = Depends(get_current_user)):
    from user_manager import UserManager

    user_manager = UserManager()
    link_code = await user_manager.generate_telegram_link_code(current_user["id"])
    if not link_code:
        raise HTTPException(status_code=500, detail="Failed to generate link code")

    return models.TelegramLinkResponse(
        link_code=link_code, instructions="Отправьте этот код в Telegram бота командой: /link <код>"
    )


@router.delete("/unlink", response_model=models.SuccessResponse)
@limiter.limit("300/minute")
async def unlink_telegram_account(current_user: dict = Depends(get_current_user)):
    from user_manager import UserManager

    user_manager = UserManager()
    success = await user_manager.unlink_telegram(current_user["id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to unlink Telegram account")

    return models.SuccessResponse(message="Telegram account successfully unlinked")


@router.get("/status", response_model=models.TelegramLinkStatusResponse)
@limiter.limit("300/minute")
async def get_telegram_link_status(current_user: dict = Depends(get_current_user)):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=500, detail="Database error")

    link = await database.get_telegram_link_status(pool, current_user["id"])
    if link:
        return models.TelegramLinkStatusResponse(
            is_linked=True, telegram_id=link.get("telegram_id"), linked_at=link.get("linked_at")
        )
    return models.TelegramLinkStatusResponse(is_linked=False)
