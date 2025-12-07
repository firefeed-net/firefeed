# tests/test_di_integration.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from di_container import setup_di_container, get_service
from interfaces import (
    IUserRepository, IRSSFeedRepository, IRSSItemRepository,
    ICategoryRepository, ISourceRepository, IApiKeyRepository, ITelegramRepository,
    IRSSFetcher, IRSSValidator, IRSSStorage, IMediaExtractor,
    ITranslationService, IDuplicateDetector, ITranslatorQueue, IMaintenanceService,
    ITelegramUserService, IWebUserService, IUserManager
)


@pytest.mark.asyncio
class TestDIIntegration:
    """Integration tests for Dependency Injection container"""

    async def test_di_container_initialization(self):
        """Test that DI container initializes without errors"""
        # This should not raise any exceptions
        setup_di_container()

    async def test_repository_interfaces_registration(self):
        """Test that all repository interfaces are properly registered"""
        setup_di_container()

        # Test repository interfaces
        user_repo = get_service(IUserRepository)
        assert user_repo is not None
        assert hasattr(user_repo, 'get_user_by_email')
        assert hasattr(user_repo, 'create_user')

        rss_feed_repo = get_service(IRSSFeedRepository)
        assert rss_feed_repo is not None
        assert hasattr(rss_feed_repo, 'create_user_rss_feed')
        assert hasattr(rss_feed_repo, 'get_user_rss_feeds')

        rss_item_repo = get_service(IRSSItemRepository)
        assert rss_item_repo is not None
        assert hasattr(rss_item_repo, 'get_all_rss_items_list')

        category_repo = get_service(ICategoryRepository)
        assert category_repo is not None
        assert hasattr(category_repo, 'get_user_categories')

        source_repo = get_service(ISourceRepository)
        assert source_repo is not None
        assert hasattr(source_repo, 'get_source_id_by_alias')

        api_key_repo = get_service(IApiKeyRepository)
        assert api_key_repo is not None
        assert hasattr(api_key_repo, 'create_user_api_key')

        telegram_repo = get_service(ITelegramRepository)
        assert telegram_repo is not None
        assert hasattr(telegram_repo, 'get_telegram_link_status')

    async def test_service_interfaces_registration(self):
        """Test that all service interfaces are properly registered"""
        setup_di_container()

        # Test service interfaces
        rss_fetcher = get_service(IRSSFetcher)
        assert rss_fetcher is not None
        assert hasattr(rss_fetcher, 'fetch_feed')

        rss_validator = get_service(IRSSValidator)
        assert rss_validator is not None
        assert hasattr(rss_validator, 'validate_feed')

        rss_storage = get_service(IRSSStorage)
        assert rss_storage is not None
        assert hasattr(rss_storage, 'save_rss_item')

        media_extractor = get_service(IMediaExtractor)
        assert media_extractor is not None
        assert hasattr(media_extractor, 'extract_image')

        translation_service = get_service(ITranslationService)
        assert translation_service is not None
        assert hasattr(translation_service, 'translate_async')

        duplicate_detector = get_service(IDuplicateDetector)
        assert duplicate_detector is not None
        assert hasattr(duplicate_detector, 'is_duplicate')

        translator_queue = get_service(ITranslatorQueue)
        assert translator_queue is not None
        assert hasattr(translator_queue, 'add_task')

        maintenance_service = get_service(IMaintenanceService)
        assert maintenance_service is not None
        assert hasattr(maintenance_service, 'cleanup_duplicates')

    async def test_user_service_interfaces_registration(self):
        """Test that user service interfaces are properly registered"""
        setup_di_container()

        # Test user service interfaces
        telegram_user_service = get_service(ITelegramUserService)
        assert telegram_user_service is not None
        assert hasattr(telegram_user_service, 'get_user_settings')

        web_user_service = get_service(IWebUserService)
        assert web_user_service is not None
        assert hasattr(web_user_service, 'generate_telegram_link_code')

        user_manager = get_service(IUserManager)
        assert user_manager is not None
        assert hasattr(user_manager, 'get_user_settings')

    async def test_repository_dependencies_injection(self):
        """Test that repositories receive proper dependencies"""
        setup_di_container()

        # Get a repository and check it has database pool
        user_repo = get_service(IUserRepository)
        assert hasattr(user_repo, 'db_pool')
        assert user_repo.db_pool is not None

    async def test_service_dependencies_injection(self):
        """Test that services receive proper dependencies"""
        setup_di_container()

        # Test RSS Manager dependencies
        from services.rss import RSSManager
        rss_manager = RSSManager(
            rss_fetcher=get_service(IRSSFetcher),
            rss_validator=get_service(IRSSValidator),
            rss_storage=get_service(IRSSStorage),
            media_extractor=get_service(IMediaExtractor),
            translation_service=get_service(ITranslationService),
            duplicate_detector=get_service(IDuplicateDetector),
            translator_queue=get_service(ITranslatorQueue),
            maintenance_service=get_service(IMaintenanceService)
        )

        assert rss_manager.rss_fetcher is not None
        assert rss_manager.rss_validator is not None
        assert rss_manager.rss_storage is not None
        assert rss_manager.media_extractor is not None
        assert rss_manager.translation_service is not None
        assert rss_manager.duplicate_detector is not None
        assert rss_manager.translator_queue is not None
        assert rss_manager.maintenance_service is not None

    async def test_config_injection(self):
        """Test that config is properly injected"""
        setup_di_container()

        # Config should be available as dict service
        config = get_service(dict)
        assert config is not None
        assert isinstance(config, dict)
        assert len(config) > 0  # Should have some configuration

    async def test_service_singleton_behavior(self):
        """Test that services behave as singletons within the same context"""
        setup_di_container()

        # Get the same service twice
        user_repo1 = get_service(IUserRepository)
        user_repo2 = get_service(IUserRepository)

        # They should be different instances (factory pattern)
        # but with same configuration
        assert user_repo1 is not user_repo2
        assert user_repo1.db_pool is user_repo2.db_pool  # Same db pool

    async def test_interface_compliance(self):
        """Test that all services implement their interfaces correctly"""
        setup_di_container()

        # Test a few key methods exist and are callable
        user_repo = get_service(IUserRepository)

        # Should have all required methods
        required_methods = [
            'get_user_by_email', 'get_user_by_id', 'create_user',
            'update_user', 'delete_user', 'save_verification_code',
            'activate_user_and_use_verification_code', 'save_password_reset_token',
            'confirm_password_reset_transaction', 'delete_password_reset_token'
        ]

        for method_name in required_methods:
            assert hasattr(user_repo, method_name)
            method = getattr(user_repo, method_name)
            assert callable(method)

    async def test_database_pool_injection(self):
        """Test that database pool is properly injected into repositories"""
        setup_di_container()

        # All repositories should have db_pool attribute
        repositories = [
            IUserRepository, IRSSFeedRepository, IRSSItemRepository,
            ICategoryRepository, ISourceRepository, IApiKeyRepository, ITelegramRepository
        ]

        for repo_interface in repositories:
            repo = get_service(repo_interface)
            assert hasattr(repo, 'db_pool')
            # db_pool should be injected during initialization
            assert repo.db_pool is not None

    async def test_error_handling_in_di(self):
        """Test error handling when services are not available"""
        # Reset DI container
        from di_container import di_container
        di_container._services.clear()
        di_container._factories.clear()

        # Try to get service without setup
        with pytest.raises(KeyError):
            get_service(IUserRepository)

        # Setup and try again
        setup_di_container()
        user_repo = get_service(IUserRepository)
        assert user_repo is not None


if __name__ == "__main__":
    # Run basic smoke test
    import asyncio

    async def smoke_test():
        print("Running DI integration smoke test...")
        setup_di_container()

        # Test basic service resolution
        user_repo = get_service(IUserRepository)
        print(f"✓ UserRepository resolved: {type(user_repo)}")

        rss_fetcher = get_service(IRSSFetcher)
        print(f"✓ RSSFetcher resolved: {type(rss_fetcher)}")

        config = get_service(dict)
        print(f"✓ Config resolved: {len(config)} keys")

        print("✓ All basic services resolved successfully")

    asyncio.run(smoke_test())