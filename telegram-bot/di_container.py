import asyncio
import aiohttp
import logging
from typing import Optional

from config import get_shared_db_pool, BOT_TOKEN, CHANNEL_IDS, CHANNEL_CATEGORIES
from firefeed_translations import get_message, LANG_NAMES, TRANSLATED_FROM_LABELS, READ_MORE_LABELS, SOURCE_LABELS
from logging_config import setup_logging
from user_manager import UserManager

from .interfaces.api_client_interface import IAPIClientService
from .interfaces.bot_interface import IBotService
from .interfaces.database_interface import IDatabaseService
from .interfaces.image_validator_interface import IImageValidatorService
from .interfaces.rss_processor_interface import IRSSProcessorService
from .interfaces.scheduler_interface import ISchedulerService
from .interfaces.user_manager_interface import IUserManagerService

from .services.api_client_service import APIClientService
from .services.bot_service import BotService
from .services.database_service import DatabaseService
from .services.image_validator_service import ImageValidatorService
from .services.rss_processor_service import RSSProcessorService
from .services.scheduler_service import SchedulerService
from .services.user_manager_service import UserManagerService

from .models.user_state import UserStateManager

logger = logging.getLogger(__name__)


class DIContainer:
    """Dependency Injection Container for Telegram Bot services."""

    def __init__(self):
        self._services = {}
        self._singletons = {}

        # Global variables as singletons
        self._singletons['http_session'] = None
        self._singletons['user_state_manager'] = UserStateManager()
        self._singletons['send_semaphore'] = asyncio.Semaphore(5)
        self._singletons['rss_item_processing_semaphore'] = asyncio.Semaphore(10)

        # Constants
        self._singletons['api_base_url'] = "http://localhost:8000/api/v1"
        self._singletons['bot_api_key'] = None  # Will be set from env
        self._singletons['bot_token'] = BOT_TOKEN
        self._singletons['channel_ids'] = CHANNEL_IDS
        self._singletons['channel_categories'] = CHANNEL_CATEGORIES

        # Translations
        self._singletons['get_message'] = get_message
        self._singletons['lang_names'] = LANG_NAMES
        self._singletons['translated_from_labels'] = TRANSLATED_FROM_LABELS
        self._singletons['read_more_labels'] = READ_MORE_LABELS
        self._singletons['source_labels'] = SOURCE_LABELS

    async def initialize(self):
        """Initialize the container and services."""
        setup_logging()
        logger.info("Initializing DI Container")

        # Initialize HTTP session
        await self._initialize_http_session()

        # Initialize UserManager
        user_manager = UserManager()
        self._singletons['user_manager'] = user_manager

        # Initialize services
        self._services['image_validator'] = ImageValidatorService()
        self._services['database'] = DatabaseService()
        self._services['api_client'] = APIClientService(
            http_session=self._singletons['http_session'],
            api_base_url=self._singletons['api_base_url'],
            bot_api_key=self._singletons['bot_api_key']
        )
        self._services['user_manager_service'] = UserManagerService(
            user_manager=user_manager,
            user_state_manager=self._singletons['user_state_manager']
        )
        self._services['bot'] = BotService(
            user_manager_service=self._services['user_manager_service'],
            database_service=self._services['database'],
            user_state_manager=self._singletons['user_state_manager'],
            send_semaphore=self._singletons['send_semaphore'],
            get_message=self._singletons['get_message'],
            lang_names=self._singletons['lang_names'],
            translated_from_labels=self._singletons['translated_from_labels'],
            read_more_labels=self._singletons['read_more_labels'],
            source_labels=self._singletons['source_labels']
        )
        self._services['rss_processor'] = RSSProcessorService(
            bot_service=self._services['bot'],
            database_service=self._services['database'],
            api_client_service=self._services['api_client'],
            image_validator_service=self._services['image_validator'],
            send_semaphore=self._singletons['send_semaphore'],
            rss_item_processing_semaphore=self._singletons['rss_item_processing_semaphore'],
            channel_categories=self._singletons['channel_categories']
        )
        self._services['scheduler'] = SchedulerService(
            rss_processor_service=self._services['rss_processor'],
            user_state_manager=self._singletons['user_state_manager']
        )

        logger.info("DI Container initialized")

    async def _initialize_http_session(self):
        """Initialize HTTP session."""
        if self._singletons['http_session'] is None:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30, keepalive_timeout=30, enable_cleanup_closed=True)
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            self._singletons['http_session'] = aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers={"User-Agent": "TelegramBot/1.0"}
            )
            logger.info("HTTP session initialized")

    async def shutdown(self):
        """Shutdown the container and clean up resources."""
        logger.info("Shutting down DI Container")

        # Close HTTP session
        if self._singletons['http_session']:
            try:
                await self._singletons['http_session'].close()
                self._singletons['http_session'] = None
                logger.info("HTTP session closed")
            except Exception as e:
                logger.error(f"Error closing HTTP session: {e}")

        # Close DB pool
        try:
            from config import close_shared_db_pool
            await close_shared_db_pool()
            logger.info("Shared DB pool closed")
        except Exception as e:
            logger.error(f"Error closing shared DB pool: {e}")

        logger.info("DI Container shut down")

    def get_service(self, service_name: str):
        """Get a service instance."""
        return self._services.get(service_name)

    def get_singleton(self, key: str):
        """Get a singleton value."""
        return self._singletons.get(key)

    # Convenience methods
    @property
    def bot_service(self) -> IBotService:
        return self._services['bot']

    @property
    def rss_processor_service(self) -> IRSSProcessorService:
        return self._services['rss_processor']

    @property
    def scheduler_service(self) -> ISchedulerService:
        return self._services['scheduler']

    @property
    def user_state_manager(self) -> UserStateManager:
        return self._singletons['user_state_manager']