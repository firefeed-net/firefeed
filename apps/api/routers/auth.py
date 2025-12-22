import logging
import random
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from apps.api.middleware import limiter
from apps.api import models
from di_container import get_service
from interfaces import IUserRepository
from apps.api.deps import create_access_token, verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from exceptions import DatabaseException
from services.email_service.sender import send_verification_email, send_registration_success_email, send_password_reset_email

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication token"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post(
    "/register",
    response_model=models.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user account with email verification.

    This endpoint creates a new user account and sends a verification email.
    The user account will remain inactive until email verification is completed.

    **Process:**
    1. Validate email format and password strength
    2. Check if email is already registered
    3. Create user account (inactive state)
    4. Generate and send verification code via email
    5. Return user information

    **Rate limit:** 5 requests per minute
    """,
    responses={
        201: {
            "description": "User successfully registered",
            "model": models.UserResponse
        },
        400: {
            "description": "Bad Request - Email already registered or invalid data",
            "model": models.HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("5/minute")
async def register_user(request: Request, user: models.UserCreate, background_tasks: BackgroundTasks):
    user_repo = get_service(IUserRepository)

    try:
        existing_user = await user_repo.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        password_hash = get_password_hash(user.password)
        new_user = await user_repo.create_user(user.email, password_hash, user.language)
        if not new_user:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

        verification_code = "".join(random.choices("0123456789", k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        ok = await user_repo.save_verification_code(new_user["id"], verification_code, expires_at)
        if not ok:
            await user_repo.delete_user(new_user["id"])
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create verification code")
    except DatabaseException as e:
        logger.error(f"Database error in register_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    async def _send_verification(email: str, code: str, lang: str):
        start_ts = datetime.now(timezone.utc)
        try:
            ok = await send_verification_email(email, code, lang)
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[VerificationEmail] Slow send: {duration:.3f}s for {email}")
            else:
                logger.info(f"[VerificationEmail] Sent in {duration:.3f}s for {email}")
            if not ok:
                logger.error(f"[VerificationEmail] Failed to send to {email}")
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            logger.error(f"[VerificationEmail] Exception after {duration:.3f}s for {email}: {e}")

    background_tasks.add_task(_send_verification, user.email, verification_code, user.language)

    return models.UserResponse(**new_user)


@router.post(
    "/verify",
    response_model=models.SuccessResponse,
    summary="Verify user email",
    description="""
    Verify user email address using the verification code sent during registration.

    This endpoint activates the user account after successful email verification.

    **Process:**
    1. Validate verification code format (6 digits)
    2. Find user by email and active verification code
    3. Activate user account
    4. Mark verification code as used

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Email successfully verified",
            "model": models.SuccessResponse
        },
        400: {
            "description": "Bad Request - Invalid verification code or email",
            "model": models.HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def verify_user(request: Request, verification_request: models.EmailVerificationRequest, background_tasks: BackgroundTasks):
    user_repo = get_service(IUserRepository)

    try:
        user = await user_repo.get_user_by_email(verification_request.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code or email")
        if user.get("is_verified"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")

        ok = await user_repo.activate_user_and_use_verification_code(user["id"], verification_request.code)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code or email")
    except DatabaseException as e:
        logger.error(f"Database error in verify_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    async def _send_registration_success(email: str, lang: str):
        start_ts = datetime.now(timezone.utc)
        try:
            ok = await send_registration_success_email(email, lang)
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[RegistrationSuccessEmail] Slow send: {duration:.3f}s for {email}")
            else:
                logger.info(f"[RegistrationSuccessEmail] Sent in {duration:.3f}s for {email}")
            if not ok:
                logger.error(f"[RegistrationSuccessEmail] Failed to send to {email}")
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            logger.error(f"[RegistrationSuccessEmail] Exception after {duration:.3f}s for {email}: {e}")

    background_tasks.add_task(_send_registration_success, verification_request.email, user.get("language", "en"))

    return models.SuccessResponse(message="User successfully verified")


@router.post(
    "/resend-verification",
    response_model=models.SuccessResponse,
    summary="Resend verification code",
    description="""
    Resend verification code to user's email if account is not verified yet.

    **Process:**
    1. Validate email exists and user is not verified
    2. Generate new verification code
    3. Send verification email

    **Rate limit:** 5 requests per minute
    """,
    responses={
        200: {
            "description": "Verification code resent",
            "model": models.SuccessResponse
        },
        400: {
            "description": "Bad Request - Email not found or already verified",
            "model": models.HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("5/minute")
async def resend_verification(request: Request, resend_request: models.ResendVerificationRequest, background_tasks: BackgroundTasks):
    user_repo = get_service(IUserRepository)

    try:
        user = await user_repo.get_user_by_email(resend_request.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found")
        if user.get("is_verified"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")

        verification_code = "".join(random.choices("0123456789", k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        ok = await user_repo.save_verification_code( user["id"], verification_code, expires_at)
        if not ok:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create verification code")
    except DatabaseException as e:
        logger.error(f"Database error in resend_verification: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    async def _send_verification(email: str, code: str, lang: str):
        start_ts = datetime.now(timezone.utc)
        try:
            ok = await send_verification_email(email, code, lang)
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[VerificationEmail] Slow send: {duration:.3f}s for {email}")
            else:
                logger.info(f"[VerificationEmail] Sent in {duration:.3f}s for {email}")
            if not ok:
                logger.error(f"[VerificationEmail] Failed to send to {email}")
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            logger.error(f"[VerificationEmail] Exception after {duration:.3f}s for {email}: {e}")

    background_tasks.add_task(_send_verification, resend_request.email, verification_code, user.get("language", "en"))

    return models.SuccessResponse(message="Verification code sent")


@router.post(
    "/login",
    response_model=models.Token,
    summary="Authenticate user",
    description="""
    Authenticate user and return JWT access token.

    This endpoint verifies user credentials and returns a JWT token for API access.
    The user account must be active (email verified) to login successfully.

    **Process:**
    1. Validate email and password
    2. Check if user exists and password is correct
    3. Verify account is active (email verified)
    4. Generate and return JWT access token

    **Token validity:** 30 minutes

    **Rate limit:** 10 requests per minute
    """,
    responses={
        200: {
            "description": "Authentication successful",
            "model": models.Token
        },
        401: {
            "description": "Unauthorized - Invalid credentials or account not verified",
            "model": models.HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("10/minute")
async def login_user(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user_repo = get_service(IUserRepository)

    try:
        user = await user_repo.get_user_by_email(form_data.username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    except DatabaseException as e:
        logger.error(f"Database error in login_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified.",
        )

    if user.get("is_deleted"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated.",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user["id"])}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60}


@router.post(
    "/reset-password/request",
    summary="Request password reset",
    description="""
    Request a password reset token to be sent to the user's email.

    This endpoint initiates the password reset process by sending a reset link
    to the user's email address. The link will be valid for 1 hour.

    **Process:**
    1. Validate email format
    2. Check if user exists (without revealing existence)
    3. Generate secure reset token
    4. Send password reset email with secure link

    **Security note:** Always returns success message regardless of email existence
    to prevent email enumeration attacks.

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Password reset email sent (if email exists)",
            "content": {
                "application/json": {
                    "example": {"message": "If email exists, reset instructions have been sent"}
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def request_password_reset(request: Request, password_reset_request: models.PasswordResetRequest, background_tasks: BackgroundTasks):
    user_repo = get_service(IUserRepository)

    try:
        user = await user_repo.get_user_by_email(password_reset_request.email)
        if not user:
            return {"message": "If email exists, reset instructions have been sent"}

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        success = await user_repo.save_password_reset_token(user["id"], token, expires_at)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create reset token")
    except DatabaseException as e:
        logger.error(f"Database error in request_password_reset: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    async def _send_and_cleanup(email: str, token: str, lang: str):
        start_ts = datetime.now(timezone.utc)
        try:
            ok = await send_password_reset_email(email, token, lang)
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            if duration > 10:
                logger.warning(f"[PasswordResetEmail] Slow send: {duration:.3f}s for {email}")
            else:
                logger.info(f"[PasswordResetEmail] Sent in {duration:.3f}s for {email}")
            if not ok:
                logger.error(f"[PasswordResetEmail] Failed to send to {email}, deleting token")
                await user_repo.delete_password_reset_token(token)
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_ts).total_seconds()
            logger.error(f"[PasswordResetEmail] Exception after {duration:.3f}s for {email}: {e}")
            try:
                await user_repo.delete_password_reset_token(token)
            except Exception as del_e:
                logger.error(f"[PasswordResetEmail] Failed to delete token on error: {del_e}")

    background_tasks.add_task(_send_and_cleanup, password_reset_request.email, token, user.get("language", "en"))

    return {"message": "If email exists, reset instructions have been sent"}


@router.post(
    "/reset-password/confirm",
    summary="Confirm password reset",
    description="""
    Confirm password reset using the token from email and set new password.

    This endpoint completes the password reset process by validating the reset token
    and updating the user's password.

    **Process:**
    1. Validate token format and new password strength
    2. Verify reset token exists and is not expired
    3. Update user password (hashed)
    4. Delete used reset token

    **Security:** Token is single-use and expires after 1 hour.

    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Password successfully reset",
            "content": {
                "application/json": {
                    "example": {"message": "Password successfully reset"}
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid or expired token",
            "model": models.HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
@limiter.limit("300/minute")
async def confirm_password_reset(request: Request, password_reset_confirm: models.PasswordResetConfirm):
    user_repo = get_service(IUserRepository)

    try:
        new_password_hash = get_password_hash(password_reset_confirm.new_password)
        ok = await user_repo.confirm_password_reset_transaction(password_reset_confirm.token, new_password_hash)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
        return {"message": "Password successfully reset"}
    except DatabaseException as e:
        logger.error(f"Database error in confirm_password_reset: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
