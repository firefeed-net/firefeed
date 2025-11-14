from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class IAPIClientService(ABC):
    @abstractmethod
    async def api_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Performs GET request to API."""
        pass

    @abstractmethod
    async def get_rss_items_list(self, display_language: Optional[str] = None, **filters) -> Dict:
        """Gets list of RSS items."""
        pass

    @abstractmethod
    async def get_rss_item_by_id(self, rss_item_id: str, display_language: str = "en") -> Dict:
        """Gets RSS item by ID."""
        pass

    @abstractmethod
    async def get_categories(self) -> List:
        """Gets list of categories."""
        pass

    @abstractmethod
    async def get_sources(self) -> List:
        """Gets list of sources."""
        pass

    @abstractmethod
    async def get_languages(self) -> List:
        """Gets list of languages."""
        pass