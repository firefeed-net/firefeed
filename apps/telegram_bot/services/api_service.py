# telegram_bot/services/api_service.py - Internal API communication service
import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)

from di_container import get_service

API_BASE_URL = None
BOT_API_KEY = None

def get_api_config():
    global API_BASE_URL, BOT_API_KEY
    if API_BASE_URL is None:
        config_obj = get_service(dict)
        API_BASE_URL = config_obj.get('API_BASE_URL', 'http://127.0.0.1:8000/api/v1')
        BOT_API_KEY = config_obj.get('BOT_API_KEY')
        # Log API key status
        logger.info(f"BOT_API_KEY configured: {'Yes' if BOT_API_KEY else 'No'}")
        logger.info(f"API_BASE_URL: {API_BASE_URL}")
    return API_BASE_URL, BOT_API_KEY

# Global HTTP session for API requests
_http_session: Optional[aiohttp.ClientSession] = None


async def get_http_session() -> aiohttp.ClientSession:
    """Get or create HTTP session for API requests."""
    global _http_session
    if _http_session is None:
        # Add retries and timeouts for more reliable connection
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30, keepalive_timeout=30, enable_cleanup_closed=True)
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        _http_session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers={"User-Agent": "TelegramBot/1.0"}
        )
    return _http_session


async def api_get(endpoint: str, params: dict = None) -> dict:
    """Performs a GET request to the API."""
    api_base_url, bot_api_key = get_api_config()
    session = await get_http_session()
    url = f"{api_base_url}{endpoint}"
    try:
        # Convert boolean parameters to strings
        if params:
            processed_params = {}
            for key, value in params.items():
                if isinstance(value, bool):
                    processed_params[key] = str(value).lower()
                else:
                    processed_params[key] = value
        else:
            processed_params = params

        # Add API key to headers if set
        headers = {}
        if bot_api_key:
            headers["X-API-Key"] = bot_api_key
            logger.debug(f"Using BOT_API_KEY for authentication: {bot_api_key[:10]}...")
        else:
            logger.warning("BOT_API_KEY is not set - API requests may fail with 401")

        logger.debug(f"Making API request to {url} with headers: {list(headers.keys())}")

        timeout = aiohttp.ClientTimeout(total=30, connect=10)  # 30 second timeout for API requests
        async with session.get(url, params=processed_params, headers=headers, timeout=timeout) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"{endpoint} returned status {response.status}")
                # Attempt to get error text for better understanding of the problem
                error_text = await response.text()
                logger.error(f"Error response body: {error_text}")
                return {}
    except asyncio.TimeoutError:
        logger.error(f"Timeout error calling {endpoint}")
        logger.error(f"API_BASE_URL: {api_base_url}, url: {url}, params: {processed_params}, headers: {headers}")
        import traceback
        logger.error(f"Timeout traceback: {traceback.format_exc()}")
        return {}
    except Exception as e:
        logger.error(f"Failed to call {endpoint}: {e}")
        return {}


async def get_rss_items_list(display_language: str = None, **filters) -> dict:
    """Gets list of RSS items."""
    params = {}
    if display_language is not None:
        params["display_language"] = display_language
    params.update(filters)
    return await api_get("/rss-items/", params)


async def get_rss_item_by_id(rss_item_id: str, display_language: str = "en") -> dict:
    """Gets RSS item by ID."""
    params = {"display_language": display_language}
    return await api_get(f"/rss-items/{rss_item_id}", params)


async def get_categories() -> list:
    """Gets list of categories."""
    result = await api_get("/categories/")
    return result.get("results", [])


async def get_sources() -> list:
    """Gets list of sources."""
    result = await api_get("/sources/")
    return result.get("results", [])


async def get_languages() -> list:
    """Gets list of languages."""
    result = await api_get("/languages/")
    return result.get("results", [])


async def close_http_session():
    """Close HTTP session."""
    global _http_session
    if _http_session:
        try:
            await _http_session.close()
            _http_session = None
            logger.info("HTTP session closed")
        except Exception as e:
            logger.error(f"Error closing HTTP session: {e}")