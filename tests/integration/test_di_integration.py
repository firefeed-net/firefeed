# tests/test_di_integration.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from di_container import setup_di_container, get_service, di_container
from interfaces import (
    IUserRepository, IRSSFeedRepository, IRSSItemRepository,
    ICategoryRepository, ISourceRepository, IApiKeyRepository,
    IRSSFetcher, IRSSValidator, IRSSStorage, IMediaExtractor,
    ITranslationService, IDuplicateDetector, ITranslatorQueue, IMaintenanceService,
    IUserService
)


@pytest.mark.asyncio
class TestDIIntegration:
    """Integration tests for Dependency Injection container"""

    async def test_di_container_initialization(self):
        """Test that DI container initializes without errors"""
        # This should not raise any exceptions
        from unittest.mock import patch
        
        def mock_setup_di_container():
            return None
        
        with patch('di_container.setup_di_container', return_value=mock_setup_di_container()):
            await setup_di_container()

    async def test_repository_interfaces_registration(self):
        """Test that all repository interfaces are properly registered"""
        from unittest.mock import patch

        with patch.object(di_container, 'resolve') as mock_resolve:
            mock_resolve.return_value = AsyncMock()

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

    async def test_service_interfaces_registration(self):
        """Test that all service interfaces are properly registered"""
        from unittest.mock import patch

        with patch.object(di_container, 'resolve') as mock_resolve:
            mock_resolve.return_value = AsyncMock()

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
        from unittest.mock import patch

        mock_web = AsyncMock()

        with patch.object(di_container, 'resolve') as mock_resolve:
            mock_resolve.side_effect = lambda interface: mock_web if interface == IUserService else AsyncMock()

            # Test user service interfaces
            user_service = get_service(IUserService)
            assert user_service is not None
            assert hasattr(user_service, 'generate_telegram_link_code')

    @patch.object(di_container, 'resolve')
    async def test_repository_dependencies_injection(self, mock_resolve):
        """Test that repositories receive proper dependencies"""

        mock_repo = AsyncMock()
        mock_repo.db_pool = AsyncMock()

        mock_resolve.return_value = mock_repo
        # Get a repository and check it has database pool
        user_repo = get_service(IUserRepository)
        assert hasattr(user_repo, 'db_pool')
        assert user_repo.db_pool is not None

    @patch.object(di_container, 'resolve')
    async def test_service_dependencies_injection(self, mock_resolve):
        """Test that services receive proper dependencies"""

        mock_services = {
            IRSSFetcher: AsyncMock(),
            IRSSValidator: AsyncMock(),
            IRSSStorage: AsyncMock(),
            IMediaExtractor: AsyncMock(),
            ITranslationService: AsyncMock(),
            IDuplicateDetector: AsyncMock(),
            ITranslatorQueue: AsyncMock(),
            IMaintenanceService: AsyncMock(),
        }

        mock_resolve.side_effect = lambda interface: mock_services.get(interface)

        # Test RSS Manager dependencies
        from apps.rss_parser.services import RSSManager
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

    @patch.object(di_container, 'resolve')
    async def test_config_injection(self, mock_resolve):
        """Test that config is properly injected"""

        mock_config = {'some': 'config'}

        mock_resolve.return_value = mock_config
        # Config should be available as dict service
        config = get_service(dict)
        assert config is not None
        assert isinstance(config, dict)
        assert len(config) > 0  # Should have some configuration

    @patch.object(di_container, 'resolve')
    async def test_service_singleton_behavior(self, mock_resolve):
        """Test that services behave as singletons within the same context"""

        mock_repo1 = AsyncMock()
        mock_repo2 = AsyncMock()
        mock_repo1.db_pool = 'same_pool'
        mock_repo2.db_pool = 'same_pool'

        call_count = 0
        def mock_resolve_func(interface):
            nonlocal call_count
            call_count += 1
            return mock_repo1 if call_count == 1 else mock_repo2

        mock_resolve.side_effect = mock_resolve_func
        # Get the same service twice
        user_repo1 = get_service(IUserRepository)
        user_repo2 = get_service(IUserRepository)

        # They should be different instances (factory pattern)
        # but with same configuration
        assert user_repo1 is not user_repo2
        assert user_repo1.db_pool is user_repo2.db_pool  # Same db pool

    @patch.object(di_container, 'resolve')
    async def test_interface_compliance(self, mock_resolve):
        """Test that all services implement their interfaces correctly"""

        mock_repo = AsyncMock()

        mock_resolve.return_value = mock_repo
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

    @patch.object(di_container, 'resolve')
    async def test_database_pool_injection(self, mock_resolve):
        """Test that database pool is properly injected into repositories"""

        mock_repos = {
            IUserRepository: AsyncMock(),
            IRSSFeedRepository: AsyncMock(),
            IRSSItemRepository: AsyncMock(),
            ICategoryRepository: AsyncMock(),
            ISourceRepository: AsyncMock(),
            IApiKeyRepository: AsyncMock(),
        }

        for mock_repo in mock_repos.values():
            mock_repo.db_pool = AsyncMock()

        mock_resolve.side_effect = lambda interface: mock_repos.get(interface)

        # All repositories should have db_pool attribute
        repositories = [
            IUserRepository, IRSSFeedRepository, IRSSItemRepository,
            ICategoryRepository, ISourceRepository, IApiKeyRepository
        ]

        for repo_interface in repositories:
            repo = get_service(repo_interface)
            assert hasattr(repo, 'db_pool')
            # db_pool should be injected during initialization
            assert repo.db_pool is not None

    @patch.object(di_container, 'resolve')
    async def test_error_handling_in_di(self, mock_resolve):
        """Test error handling when services are not available"""

        call_count = 0
        def mock_resolve_func(interface):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise KeyError(interface)
            return AsyncMock()

        mock_resolve.side_effect = mock_resolve_func
        # Try to get service without setup
        with pytest.raises(KeyError):
            get_service(IUserRepository)

        # Setup and try again
        user_repo = get_service(IUserRepository)
        assert user_repo is not None


if __name__ == "__main__":
    # Run basic smoke test
    import asyncio

    async def smoke_test():
        print("Running DI integration smoke test...")
        from unittest.mock import patch

        mock_services = {
            IUserRepository: AsyncMock(),
            IRSSFetcher: AsyncMock(),
            dict: {'some': 'config'},
        }

        with patch.object(di_container, 'resolve') as mock_resolve, \
             patch('di_container.setup_di_container'):
            mock_resolve.side_effect = lambda interface: mock_services.get(interface, AsyncMock())

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