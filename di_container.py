# di_container.py - Dependency Injection Container
import logging
from typing import Dict, Any, Type, TypeVar, Optional
from interfaces import (
    IRSSFetcher, IRSSValidator, IRSSStorage, IMediaExtractor, ITranslationService,
    ITranslationCache, IDuplicateDetector, ITranslatorQueue, IMaintenanceService,
    ITelegramUserService, IWebUserService, IUserRepository, IRSSFeedRepository,
    IRSSItemRepository, ICategoryRepository, ISourceRepository, IApiKeyRepository,
    ITelegramRepository, IDatabasePool, IModelManager
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """Simple Dependency Injection Container"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}

    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> None:
        """Register a service implementation"""
        if singleton:
            self._services[interface] = implementation
        else:
            self._factories[interface] = implementation

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance"""
        self._singletons[interface] = instance

    def register_factory(self, interface: Type[T], factory: callable) -> None:
        """Register a factory function"""
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance"""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check services
        if interface in self._services:
            impl_class = self._services[interface]
            instance = self._instantiate(impl_class)
            self._singletons[interface] = instance  # Cache as singleton
            return instance

        # Check factories
        if interface in self._factories:
            factory = self._factories[interface]
            return factory()

        raise ValueError(f"No registration found for {interface}")

    def _instantiate(self, cls: Type[T]) -> T:
        """Instantiate a class with dependency injection"""
        import inspect

        # Get constructor parameters
        init_signature = inspect.signature(cls.__init__)
        params = {}

        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue

            # Skip *args and **kwargs parameters
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Try to resolve parameter type
            if param.annotation != inspect.Parameter.empty:
                try:
                    params[param_name] = self.resolve(param.annotation)
                except ValueError:
                    # If can't resolve, try to get default value
                    if param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                    else:
                        raise ValueError(f"Cannot resolve parameter {param_name} for {cls}")
            elif param.default != inspect.Parameter.empty:
                params[param_name] = param.default
            else:
                raise ValueError(f"Cannot resolve parameter {param_name} for {cls}")

        # If no parameters needed, just instantiate
        if not params:
            return cls()

        return cls(**params)

    def clear(self) -> None:
        """Clear all registrations and instances"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()


# Global DI container instance
di_container = DIContainer()


async def setup_di_container() -> DIContainer:
    """Setup the global DI container with all services"""
    global di_container

    # Import configuration
    from config.services_config import get_service_config

    config = get_service_config()

    # Register config as both dict and ServiceConfig first
    di_container.register_instance(dict, config)
    di_container.register_instance(type(config), config)

    # Import services
    from services.rss import MediaExtractor, RSSValidator, RSSStorage, RSSFetcher
    from services.translation import ModelManager, TranslationService, TranslationCache
    from services.translation.task_queue import FireFeedTranslatorTaskQueue
    from services.text_analysis.duplicate_detector import FireFeedDuplicateDetector
    from services.database_pool_adapter import DatabasePoolAdapter
    from services.maintenance_service import MaintenanceService
    from services.user import TelegramUserService, WebUserService

    # Register database pool adapter
    # For testing/development, create a mock pool if database is not available
    try:
        # Create database pool using config
        import aiopg

        db_config = {
            "host": config.database.host,
            "user": config.database.user,
            "password": config.database.password,
            "database": config.database.name,
            "port": config.database.port,
            "minsize": config.database.minsize,
            "maxsize": config.database.maxsize,
        }

        # Log database connection config for debugging
        masked_config = db_config.copy()
        masked_config["password"] = "***" if db_config["password"] else None
        logger.info(f"Database connection config: {masked_config}")

        db_pool = await aiopg.create_pool(**db_config)

        db_pool_adapter = DatabasePoolAdapter(db_pool)
        di_container.register_instance(IDatabasePool, db_pool_adapter)
    except Exception as e:
        logger.warning(f"Database not available, creating mock pool: {e}")
        # Create mock pool for testing/development
        class MockPool:
            def acquire(self):
                class MockConn:
                    def __await__(self):
                        async def _await():
                            return self
                        return _await().__await__()
                    def cursor(self):
                        class MockCursor:
                            rowcount = 0
                            description = []
                            async def execute(self, *args, **kwargs): pass
                            async def fetchone(self): return None
                            async def fetchall(self): return []
                            def __aiter__(self): return self
                            async def __anext__(self): raise StopAsyncIteration
                            async def __aenter__(self): return self
                            async def __aexit__(self, *args): pass
                        return MockCursor()
                    async def __aenter__(self): return self
                    async def __aexit__(self, *args): pass
                return MockConn()
            def release(self, conn): pass
            async def close(self): pass
            async def wait_closed(self): pass

        db_pool = MockPool()
        db_pool_adapter = DatabasePoolAdapter(db_pool)
        di_container.register_instance(IDatabasePool, db_pool_adapter)

    # Register Redis client
    import redis
    redis_client = redis.Redis(
        host=config.redis.host,
        port=config.redis.port,
        username=config.redis.username,
        password=config.redis.password,
        db=config.redis.db,
        decode_responses=True
    )
    di_container.register_instance(redis.Redis, redis_client)

    # Register repositories
    from repositories import (
        UserRepository, RSSFeedRepository, RSSItemRepository,
        CategoryRepository, SourceRepository, ApiKeyRepository, TelegramRepository
    )
    from interfaces import (
        IUserRepository, IRSSFeedRepository, IRSSItemRepository,
        ICategoryRepository, ISourceRepository, IApiKeyRepository, ITelegramRepository
    )

    di_container.register_factory(IUserRepository, lambda: UserRepository(db_pool_adapter))
    di_container.register_factory(IRSSFeedRepository, lambda: RSSFeedRepository(db_pool_adapter))
    di_container.register_factory(IRSSItemRepository, lambda: RSSItemRepository(db_pool_adapter))
    di_container.register_factory(ICategoryRepository, lambda: CategoryRepository(db_pool_adapter))
    di_container.register_factory(ISourceRepository, lambda: SourceRepository(db_pool_adapter))
    di_container.register_factory(IApiKeyRepository, lambda: ApiKeyRepository(db_pool_adapter))
    di_container.register_factory(ITelegramRepository, lambda: TelegramRepository(db_pool_adapter))

    # Register simple services first
    di_container.register(IRSSStorage, RSSStorage)
    di_container.register(IMediaExtractor, MediaExtractor)

    # Register RSS services with configuration (after dependencies)
    di_container.register_factory(IRSSFetcher, lambda: RSSFetcher(
        media_extractor=di_container.resolve(IMediaExtractor),
        duplicate_detector=di_container.resolve(IDuplicateDetector),
        max_concurrent_feeds=getattr(config.rss, 'max_concurrent_feeds', 10),
        max_entries_per_feed=getattr(config.rss, 'max_entries_per_feed', 50)
    ))

    di_container.register_factory(IRSSValidator, lambda: RSSValidator(
        cache_ttl=getattr(config.rss, 'validation_cache_ttl', 300),
        request_timeout=getattr(config.rss, 'request_timeout', 15)
    ))

    # Register translation services with configuration
    di_container.register_factory(IModelManager, lambda: ModelManager(
        device=getattr(config.translation, 'default_device', 'cpu'),
        max_cached_models=getattr(config.translation, 'max_cached_models', 15),
        model_cleanup_interval=getattr(config.translation, 'model_cleanup_interval', 1800)
    ))

    # Create translator queue first
    translator_queue = FireFeedTranslatorTaskQueue(
        translator=None,  # Will be set later
        max_workers=getattr(config.queue, 'default_workers', 1),
        queue_size=getattr(config.queue, 'max_queue_size', 30)
    )
    di_container.register_instance(ITranslatorQueue, translator_queue)

    # Create translation service
    translation_service = TranslationService(
        model_manager=di_container.resolve(IModelManager),
        translator_queue=translator_queue,
        max_concurrent_translations=getattr(config.translation, 'max_concurrent_translations', 3)
    )
    di_container.register_instance(ITranslationService, translation_service)

    # Set translation service as translator for the queue
    translator_queue.set_translator(translation_service)

    di_container.register_factory(ITranslationCache, lambda: TranslationCache(
        default_ttl=getattr(config.cache, 'default_ttl', 3600),
        max_size=getattr(config.cache, 'max_cache_size', 10000)
    ))

    di_container.register_factory(IDuplicateDetector, lambda: FireFeedDuplicateDetector(di_container.resolve(IRSSItemRepository)))

    # Register maintenance service
    di_container.register_factory(IMaintenanceService, lambda: MaintenanceService(db_pool))

    # Register user services
    di_container.register_factory(ITelegramUserService, lambda: TelegramUserService(di_container.resolve(IUserRepository)))
    di_container.register_factory(IWebUserService, lambda: WebUserService(di_container.resolve(IUserRepository)))

    logger.info("DI container setup completed with configuration")
    return di_container


def get_service(interface: Type[T]) -> T:
    """Get a service instance from the global DI container"""
    return di_container.resolve(interface)


async def get_db_pool():
    """Get database pool instance from DI container"""
    db_pool_adapter = get_service(IDatabasePool)
    # Return the actual pool from the adapter
    async with db_pool_adapter.acquire() as conn:
        # This is a bit hacky, but we need to return the pool, not a connection
        # The adapter's _pool attribute contains the actual aiopg pool
        return db_pool_adapter._pool