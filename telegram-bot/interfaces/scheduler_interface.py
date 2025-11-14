from abc import ABC, abstractmethod
from telegram.ext import ContextTypes


class ISchedulerService(ABC):
    @abstractmethod
    async def monitor_rss_items_task(self, context: ContextTypes.DEFAULT_TYPE):
        """Task to monitor RSS items."""
        pass

    @abstractmethod
    async def cleanup_expired_user_data(self, context=None):
        """Task to clean expired user data."""
        pass