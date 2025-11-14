from abc import ABC, abstractmethod
from typing import Dict, Optional


class IRSSProcessorService(ABC):
    @abstractmethod
    async def process_rss_item(self, context, rss_item_from_api, subscribers_cache=None, channel_categories_cache=None) -> bool:
        """Processes RSS item received from API."""
        pass

    @abstractmethod
    async def monitor_rss_items_task(self, context):
        """Monitors RSS items from API."""
        pass