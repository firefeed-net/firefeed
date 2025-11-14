import aiohttp
import logging
from typing import Dict, List, Optional

from ..interfaces.api_client_interface import IAPIClientService

logger = logging.getLogger(__name__)


class APIClientService(IAPIClientService):
    """Service for API client operations."""

    def __init__(self, http_session: aiohttp.ClientSession, api_base_url: str, bot_api_key: Optional[str] = None):
        self.http_session = http_session
        self.api_base_url = api_base_url
        self.bot_api_key = bot_api_key

    async def api_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Performs GET request to API."""
        if self.http_session is None:
            raise RuntimeError("HTTP session not initialized")

        url = f"{self.api_base_url}{endpoint}"
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
            if self.bot_api_key:
                headers["X-API-Key"] = self.bot_api_key

            timeout = aiohttp.ClientTimeout(total=10, connect=5)  # 10 second timeout for API requests
            async with self.http_session.get(url, params=processed_params, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"{endpoint} returned status {response.status}")
                    # Attempt to get error text for better understanding of the problem
                    error_text = await response.text()
                    logger.error(f"Error response body: {error_text}")
                    return {}
        except aiohttp.ClientTimeout:
            logger.error(f"Timeout error calling {endpoint}")
            return {}
        except Exception as e:
            logger.error(f"Failed to call {endpoint}: {e}")
            return {}

    async def get_rss_items_list(self, display_language: Optional[str] = None, **filters) -> Dict:
        """Gets list of RSS items."""
        params = {}
        if display_language is not None:
            params["display_language"] = display_language
        params.update(filters)
        return await self.api_get("/rss-items/", params)

    async def get_rss_item_by_id(self, rss_item_id: str, display_language: str = "en") -> Dict:
        """Gets RSS item by ID."""
        params = {"display_language": display_language}
        return await self.api_get(f"/rss-items/{rss_item_id}", params)

    async def get_categories(self) -> List:
        """Gets list of categories."""
        result = await self.api_get("/categories/")
        return result.get("results", [])

    async def get_sources(self) -> List:
        """Gets list of sources."""
        result = await self.api_get("/sources/")
        return result.get("results", [])

    async def get_languages(self) -> List:
        """Gets list of languages."""
        result = await self.api_get("/languages/")
        return result.get("results", [])