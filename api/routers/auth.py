import logging
import random
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from api.middleware import limiter
from api import database, models
from api.deps import create_access_token, verify_password, get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_user(request: Request, user: models.UserCreate, background_tasks: BackgroundTasks):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    existing_user = await database.get_user_by_email(pool, user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    password_hash = get_password_hash(user.password)
    new_user = await database.create_user(pool, user.email, password_hash, user.language)
    if not new_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    verification_code = "".join(random.choices("0123456789", k=6))
    expires_at = datetime.utcnow() + timedelta(hours=24)
    ok = await database.save_verification_code(pool, new_user["id"], verification_code, expires_at)
    if not ok:
        await database.delete_user(pool, new_user["id"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create verification code")

    from email_service.sender import send_verification_email

    async def _send_verification(email: str, code: str, lang: str):
        start_ts = datetime.utcnow()
        try:
            ok = await send_verification_email(email, code, lang)
            duration = (datetime.utcnow() - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[VerificationEmail] Slow send: {duration:.3f}s for {email}")
            else:
                logger.info(f"[VerificationEmail] Sent in {duration:.3f}s for {email}")
            if not ok:
                logger.error(f"[VerificationEmail] Failed to send to {email}")
        except Exception as e:
            duration = (datetime.utcnow() - start_ts).total_seconds()
            logger.error(f"[VerificationEmail] Exception after {duration:.3f}s for {email}: {e}")

    background_tasks.add_task(_send_verification, user.email, verification_code, user.language)

    return models.UserResponse(**new_user)


@router.post("/verify", response_model=models.SuccessResponse)
@limiter.limit("300/minute")
async def verify_user(request: models.EmailVerificationRequest):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    user = await database.get_user_by_email(pool, request.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code or email")
    if user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")

    ok = await database.activate_user_and_use_verification_code(pool, user["id"], request.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code or email")

    return models.SuccessResponse(message="User successfully verified")


@router.post("/login", response_model=models.Token)
@limiter.limit("10/minute")
async def login_user(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    user = await database.get_user_by_email(pool, form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified. Please check your email for verification code.",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user["id"])}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60}


@router.post("/reset-password/request")
@limiter.limit("300/minute")
async def request_password_reset(request: models.PasswordResetRequest, background_tasks: BackgroundTasks):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    user = await database.get_user_by_email(pool, request.email)
    if not user:
        return {"message": "If email exists, reset instructions have been sent"}

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    success = await database.save_password_reset_token(pool, user["id"], token, expires_at)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create reset token")

    from email_service.sender import send_password_reset_email

    async def _send_and_cleanup(email: str, token: str, lang: str):
        start_ts = datetime.utcnow()
        try:
            ok = await send_password_reset_email(email, token, lang)
            duration = (datetime.utcnow() - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[PasswordResetEmail] Slow send: {duration:.3f}s for {email}")
            else:
                logger.info(f"[PasswordResetEmail] Sent in {duration:.3f}s for {email}")
            if not ok:
                logger.error(f"[PasswordResetEmail] Failed to send to {email}, deleting token")
                await database.delete_password_reset_token(pool, token)
        except Exception as e:
            duration = (datetime.utcnow() - start_ts).total_seconds()
            logger.error(f"[PasswordResetEmail] Exception after {duration:.3f}s for {email}: {e}")
            try:
                await database.delete_password_reset_token(pool, token)
            except Exception as del_e:
                logger.error(f"[PasswordResetEmail] Failed to delete token on error: {del_e}")

    background_tasks.add_task(_send_and_cleanup, request.email, token, user.get("language", "en"))

    return {"message": "If email exists, reset instructions have been sent"}


@router.post("/reset-password/confirm")
@limiter.limit("300/minute")
async def confirm_password_reset(request: models.PasswordResetConfirm):
    pool = await database.get_db_pool()
    if pool is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    new_password_hash = get_password_hash(request.new_password)
    ok = await database.confirm_password_reset_transaction(pool, request.token, new_password_hash)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    return {"message": "Password successfully reset"}
