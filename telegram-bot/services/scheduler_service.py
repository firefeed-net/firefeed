import logging
from telegram.ext import ContextTypes

from ..interfaces.scheduler_interface import ISchedulerService
from ..interfaces.rss_processor_interface import IRSSProcessorService
from ..models.user_state import UserStateManager

logger = logging.getLogger(__name__)


class SchedulerService(ISchedulerService):
    """Service for scheduling tasks."""

    def __init__(self, rss_processor_service: IRSSProcessorService, user_state_manager: UserStateManager):
        self.rss_processor_service = rss_processor_service
        self.user_state_manager = user_state_manager

    async def monitor_rss_items_task(self, context: ContextTypes.DEFAULT_TYPE):
        """Task to monitor RSS items."""
        await self.rss_processor_service.monitor_rss_items_task(context)

    async def cleanup_expired_user_data(self, context=None):
        """Task to clean expired user data."""
        self.user_state_manager.cleanup_expired_data()