import logging
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import bcrypt
import jwt
import redis
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from di_container import get_service
from interfaces import IUserRepository, IApiKeyRepository

logger = logging.getLogger(__name__)

# Config will be loaded lazily when needed
_config = None

def get_config():
    """Get config from DI container lazily"""
    global _config
    if _config is None:
        _config = get_service(dict)
    return _config

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Fallback for initial load
ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

security = HTTPBearer()


def hash_api_key(api_key: str) -> str:
    """Hash API key with bcrypt for storage"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(api_key.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    config = get_config()
    secret_key = config.get('JWT_SECRET_KEY', SECRET_KEY)
    algorithm = config.get('JWT_ALGORITHM', ALGORITHM)

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    try:
        config = get_config()
        secret_key = config.get('JWT_SECRET_KEY', SECRET_KEY)
        algorithm = config.get('JWT_ALGORITHM', ALGORITHM)

        payload = jwt.decode(credentials.credentials, secret_key, algorithms=[algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Get full user data from database
        user_repo = get_service(IUserRepository)
        user_data = await user_repo.get_user_by_id(int(user_id))
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def sanitize_search_phrase(search_phrase: str) -> str:
    """Sanitize search phrase to prevent injection and limit length"""
    if not search_phrase:
        return ""

    # Remove potentially dangerous characters and limit length
    sanitized = re.sub(r'[^\w\s\-.,!?\'"()\[\]{}]', '', search_phrase)
    return sanitized.strip()[:200]  # Limit to 200 characters


def validate_rss_url(url: str) -> bool:
    """Validate RSS URL format and safety"""
    if not url or len(url) > 2048:
        return False

    try:
        parsed = urlparse(url)
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        # Only allow http/https
        if parsed.scheme not in ['http', 'https']:
            return False
        # Basic domain validation
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', parsed.netloc.split(':')[0]):
            return False
        return True
    except Exception:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def format_datetime(dt_obj):
    return dt_obj.isoformat() if dt_obj else None


def get_full_image_url(image_filename: str) -> str:
    if not image_filename:
        return None
    if image_filename.startswith(("http://", "https://")):
        return image_filename
    config = get_config()
    base_url = config.get('HTTP_IMAGES_ROOT_DIR', '').rstrip("/")
    filename = image_filename.lstrip("/")
    return f"{base_url}/{filename}"


def build_translations_dict(row_dict):
    translations = {}
    languages = ["ru", "en", "de", "fr"]
    original_language = row_dict.get("original_language")

    for lang in languages:
        title_key = f"title_{lang}"
        content_key = f"content_{lang}"
        title = row_dict.get(title_key)
        content = row_dict.get(content_key)
        if title is not None or content is not None:
            translations[lang] = {"title": title, "content": content}

    return translations


def validate_rss_items_query_params(from_date, cursor_created_at):

    from_datetime = None
    if from_date is not None:
        try:
            from_datetime = datetime.fromtimestamp(from_date / 1000.0)
        except (ValueError, OSError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp format in from_date parameter"
            )

    before_created_at = None
    if cursor_created_at is not None:
        try:
            before_created_at = datetime.fromtimestamp(cursor_created_at / 1000.0)
        except (ValueError, OSError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timestamp format in cursor_created_at parameter",
            )

    return from_datetime, before_created_at


# Redis client for rate limiting
_redis_client = None


def get_redis_client():
    """Get Redis client for rate limiting"""
    global _redis_client
    if _redis_client is None:
        config = get_config()
        redis_config = config.get('REDIS_CONFIG', {})
        _redis_client = redis.Redis(
            host=redis_config.get("host", "localhost"),
            port=redis_config.get("port", 6379),
            username=redis_config.get("username"),
            password=redis_config.get("password"),
            db=redis_config.get("db", 0),
            decode_responses=True
        )
    return _redis_client


async def check_rate_limit(api_key_data: Dict[str, Any]) -> None:
    """Check and increment rate limit for API key"""
    redis_client = get_redis_client()
    key_id = api_key_data["id"]
    limits = api_key_data["limits"]

    now = datetime.utcnow()
    day_key = f"user_api_key:{key_id}:day:{now.strftime('%Y-%m-%d')}"
    hour_key = f"user_api_key:{key_id}:hour:{now.strftime('%Y-%m-%d-%H')}"

    # Check daily limit
    if "requests_per_day" in limits:
        day_count = redis_client.incr(day_key)
        if day_count == 1:
            redis_client.expire(day_key, 86400)  # 24 hours
        if day_count > limits["requests_per_day"]:
            logger.warning(f"API key {key_id}: Daily limit exceeded ({day_count}/{limits['requests_per_day']})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily request limit exceeded",
                headers={"Retry-After": "86400"}
            )
        logger.info(f"API key {key_id}: Daily requests {day_count}/{limits['requests_per_day']}")

    # Check hourly limit
    if "requests_per_hour" in limits:
        hour_count = redis_client.incr(hour_key)
        if hour_count == 1:
            redis_client.expire(hour_key, 3600)  # 1 hour
        if hour_count > limits["requests_per_hour"]:
            logger.warning(f"API key {key_id}: Hourly limit exceeded ({hour_count}/{limits['requests_per_hour']})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Hourly request limit exceeded",
                headers={"Retry-After": "3600"}
            )
        logger.info(f"API key {key_id}: Hourly requests {hour_count}/{limits['requests_per_hour']}")


async def get_current_user_by_api_key(request: Request):
    """Dependency to get current user authenticated by API key"""
    try:
        # Extract API key from X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-API-Key header required",
            )

        config = get_config()
        logger.info(f"[API_KEY_AUTH] Received API key: {api_key}")
        site_api_key = config.get('SITE_API_KEY')
        logger.info(f"[API_KEY_AUTH] SITE_API_KEY from config: {site_api_key}")

        # Get BOT_API_KEY from environment (used by telegram_bot)
        bot_api_key = os.getenv("BOT_API_KEY")
        logger.info(f"[API_KEY_AUTH] BOT_API_KEY from env: {bot_api_key[:10] if bot_api_key else 'None'}...")

        # Check if it's the site or bot API key
        if site_api_key and api_key == site_api_key:
            logger.info("[API_KEY_AUTH] SITE_API_KEY matched - authenticating as system user")
            # Site key: unlimited access, return system user
            return {
                "id": 0,  # System user ID
                "email": "system@firefeed.net",
                "language": "en",
                "is_active": True,
                "created_at": None,
                "updated_at": None,
                "api_key_data": {"limits": {}}  # No limits
            }
        if bot_api_key and api_key == bot_api_key:
            logger.info(f"[API_KEY_AUTH] BOT_API_KEY matched - received: {api_key[:10]}..., configured: {bot_api_key[:10]}...")
            # Bot key: unlimited access, return bot user
            return {
                "id": -1,  # Bot user ID
                "email": "bot@firefeed.net",
                "language": "en",
                "is_active": True,
                "created_at": None,
                "updated_at": None,
                "api_key_data": {"limits": {}}  # No limits
            }
        else:
            logger.warning(f"[API_KEY_AUTH] BOT_API_KEY not matched - received: {api_key[:10]}..., configured: {bot_api_key[:10] if bot_api_key else 'None'}")

        logger.info("[API_KEY_AUTH] No special API key match, checking user API keys")

        # Get API key data from database
        api_key_repo = get_service(IApiKeyRepository)
        user_repo = get_service(IUserRepository)

        api_key_data = await api_key_repo.get_user_api_key_by_key(api_key)
        if not api_key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check rate limits
        await check_rate_limit(api_key_data)

        # Get user data
        user_data = await user_repo.get_user_by_id(api_key_data["user_id"])
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is verified and not deleted
        if not user_data.get("is_verified") or user_data.get("is_deleted"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not verified or deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return user data with API key info
        user_data["api_key_data"] = api_key_data
        return user_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in API key authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
