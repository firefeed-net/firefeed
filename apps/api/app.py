import asyncio
import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from di_container import get_service, setup_di_container
from interfaces import IUserRepository

from apps.api.middleware import setup_middleware
from apps.api.routers import auth as auth_router
from apps.api.routers import users as users_router
from apps.api.routers import categories as categories_router
from apps.api.routers import rss_feeds as rss_feeds_router
from apps.api.routers import telegram as telegram_router
from apps.api.routers import rss_items as rss_items_router
from apps.api.routers import rss as rss_router
from apps.api.routers import api_keys as api_keys_router
from apps.api.websocket import router as ws_router, check_for_new_rss_items
from utils.cleanup import periodic_cleanup_users
from config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Setup DI container
    await setup_di_container()
    
    # Start background rss items checking task
    asyncio.create_task(check_for_new_rss_items())
    logger.info("[Startup] RSS items checking task started")
    
    # Start background user cleanup task
    asyncio.create_task(periodic_cleanup_users())
    logger.info("[Startup] User cleanup task started")
    
    yield
    
    # Shutdown
    try:
        user_repo = get_service(IUserRepository)
        await user_repo.db_pool.close()
        logger.info("[Shutdown] Database pool closed")
    except Exception as e:
        logger.error(f"[Shutdown] Error closing DB pool: {e}")


app = FastAPI(
    title="FireFeed API",
    description="""
    # FireFeed News Aggregator API

    A comprehensive AI-powered news aggregation platform that collects, processes, and distributes news from RSS feeds in multiple languages.

    ## Features

    * **AI-Powered Content Processing**: Automatic translation to 4 languages (Russian, German, French, English) using modern ML models
    * **Duplicate Detection**: Semantic analysis using vector embeddings to identify duplicate content
    * **Multi-language Support**: Full localization for Telegram bot and REST API
    * **Personalized Feeds**: User-specific RSS feed subscriptions with category filtering
    * **Real-time Updates**: WebSocket support for live news updates
    * **Secure Authentication**: JWT-based authentication with email verification

    ## Authentication

    All endpoints except `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/reset-password/request`, and `/api/v1/auth/verify` require authentication.

    Include the JWT token in the Authorization header:
    ```
    Authorization: Bearer <your_jwt_token>
    ```

    ## Rate Limiting

    API endpoints are protected with rate limiting:
    - Authentication endpoints: 5-300 requests per minute
    - General endpoints: 100-300 requests per minute

    ## Response Codes

    - `200`: Success
    - `201`: Created
    - `400`: Bad Request
    - `401`: Unauthorized
    - `403`: Forbidden
    - `404`: Not Found
    - `429`: Too Many Requests
    - `500`: Internal Server Error
    """,
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    contact={
        "name": "FireFeed Support",
        "url": "https://firefeed.net",
        "email": "support@firefeed.net",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Middleware & rate limiting
setup_middleware(app)

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "https://firefeed.net",
    "https://www.firefeed.net",
]
if os.getenv("ENVIRONMENT") == "production":
    origins = [
        "https://firefeed.net",
        "https://www.firefeed.net",
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
# Users router has placeholder dependency; keep disabled until wired with auth dep
app.include_router(users_router.router)
# Attach routers with new module names
app.include_router(categories_router.router)
app.include_router(rss_feeds_router.router)
app.include_router(telegram_router.router)
app.include_router(rss_items_router.router)
app.include_router(rss_router.router)
app.include_router(api_keys_router.router)
app.include_router(ws_router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
