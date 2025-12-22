import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.maintenance_service import MaintenanceService
from exceptions import DatabaseException, ServiceUnavailableException


@pytest.fixture
def mock_db_pool():
    return AsyncMock()


@pytest.fixture
def service(mock_db_pool):
    return MaintenanceService(mock_db_pool)


class TestMaintenanceService:
    @pytest.mark.asyncio
    async def test_cleanup_duplicates_success(self, service, mock_db_pool):
        mock_conn = AsyncMock()
        mock_cur = AsyncMock()
        mock_cur.rowcount = 5
        
        # Set up the async context manager for acquire()
        class MockAcquireContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Set up the async context manager for cursor()
        class MockCursorContextManager:
            async def __aenter__(self):
                return mock_cur
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Mock the acquire method to return the context manager
        mock_db_pool.acquire = MagicMock(return_value=MockAcquireContextManager())
        mock_conn.cursor = MagicMock(return_value=MockCursorContextManager())

        await service.cleanup_duplicates()

        mock_cur.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_duplicates_failure(self, service, mock_db_pool):
        mock_conn = AsyncMock()
        mock_cur = AsyncMock()
        mock_cur.execute.side_effect = Exception("DB error")
        
        # Set up the async context manager for acquire()
        class MockAcquireContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Set up the async context manager for cursor()
        class MockCursorContextManager:
            async def __aenter__(self):
                return mock_cur
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Mock the acquire method to return the context manager
        mock_db_pool.acquire = MagicMock(return_value=MockAcquireContextManager())
        mock_conn.cursor = MagicMock(return_value=MockCursorContextManager())

        with pytest.raises(DatabaseException):
            await service.cleanup_duplicates()

    @pytest.mark.asyncio
    async def test_cleanup_old_data_by_age_success(self, service, mock_db_pool):
        mock_rss_repo = AsyncMock()
        mock_rss_repo.cleanup_old_rss_items.return_value = (10, [("img1.jpg", "vid1.mp4"), ("img2.jpg", None)], True)

        mock_config = MagicMock()
        mock_config.images_root_dir = "/tmp/images"
        mock_config.videos_root_dir = "/tmp/videos"

        with patch('repositories.rss_item_repository.RSSItemRepository', return_value=mock_rss_repo), \
             patch('services.maintenance_service.get_service_config', return_value=mock_config), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:

            result = await service.cleanup_old_data_by_age(24)

            assert result["news_items_deleted"] == 10
            assert result["images_deleted"] == 2
            assert result["videos_deleted"] == 1
            assert result["transaction_success"] is True
            assert mock_remove.call_count == 3

    @pytest.mark.asyncio
    async def test_cleanup_old_data_by_age_db_failure(self, service, mock_db_pool):
        mock_rss_repo = AsyncMock()
        mock_rss_repo.cleanup_old_rss_items.return_value = (0, [], False)

        with patch('repositories.rss_item_repository.RSSItemRepository', return_value=mock_rss_repo):
            with pytest.raises(DatabaseException):
                await service.cleanup_old_data_by_age(24)

    @pytest.mark.asyncio
    async def test_cleanup_old_data_by_age_file_cleanup_failure(self, service, mock_db_pool):
        mock_rss_repo = AsyncMock()
        mock_rss_repo.cleanup_old_rss_items.return_value = (5, [("img1.jpg", "vid1.mp4")], True)

        mock_config = MagicMock()
        mock_config.images_root_dir = "/tmp/images"
        mock_config.videos_root_dir = "/tmp/videos"

        with patch('repositories.rss_item_repository.RSSItemRepository', return_value=mock_rss_repo), \
             patch('services.maintenance_service.get_service_config', return_value=mock_config), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove', side_effect=Exception("File error")):

            result = await service.cleanup_old_data_by_age(24)

            assert result["files_failed_to_delete"] == 2