import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from di_container import di_container
from datetime import datetime, timedelta, timezone
from utils.db_pool import get_db_pool, close_db_pool
from repositories import UserRepository, ApiKeyRepository, RSSFeedRepository, CategoryRepository, SourceRepository, RSSItemRepository


@pytest.mark.anyio
class TestDatabasePool:
    async def test_get_db_pool_success(self):
        mock_config = MagicMock()
        mock_config.get = MagicMock(return_value=AsyncMock(return_value="mock_pool"))
        with patch.object(di_container, 'resolve', return_value=mock_config):
            result = await get_db_pool()
            assert result == "mock_pool"

    async def test_get_db_pool_failure(self):
        with patch('utils.db_pool.get_service', return_value={'get_shared_db_pool': lambda: (_ for _ in ()).throw(Exception("DB error"))}):
            result = await get_db_pool()
            assert result is None

    async def test_close_db_pool_success(self):
        mock_config = MagicMock()
        async def mock_close_db_pool():
            pass
        mock_config.get = MagicMock(return_value=mock_close_db_pool)
        with patch.object(di_container, 'resolve', return_value=mock_config):
            await close_db_pool()

    async def test_close_db_pool_failure(self):
        mock_config = MagicMock()
        async def mock_get_close_db_pool():
            raise Exception("DB error")
        mock_config.get = MagicMock(return_value=mock_get_close_db_pool)
        with patch.object(di_container, 'resolve', return_value=mock_config):
            await close_db_pool()


@pytest.mark.anyio
class TestUserRepository:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        return pool

    async def test_create_user_success(self, mock_pool):
        expected_result = {
            'id': 1, 'email': 'test@example.com', 'language': 'en',
            'is_active': False, 'is_verified': False, 'created_at': datetime.now(timezone.utc)
        }
        repo = UserRepository(mock_pool)
        with patch.object(repo, 'create_user', return_value=expected_result) as mock_create:
            result = await repo.create_user('test@example.com', 'hashed_pass', 'en')
            mock_create.assert_called_once_with('test@example.com', 'hashed_pass', 'en')
            assert result['email'] == 'test@example.com'

    async def test_get_user_by_email_success(self, mock_pool):
        expected_result = {
            'id': 1, 'email': 'test@example.com', 'password_hash': 'hashed_pass',
            'language': 'en', 'is_active': True, 'is_verified': False, 'is_deleted': False,
            'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)
        }
        repo = UserRepository(mock_pool)
        with patch.object(repo, 'get_user_by_email', return_value=expected_result) as mock_get:
            result = await repo.get_user_by_email('test@example.com')
            mock_get.assert_called_once_with('test@example.com')
            assert result['email'] == 'test@example.com'

    async def test_get_user_by_id_success(self, mock_pool):
        expected_result = {
            'id': 1, 'email': 'test@example.com', 'password_hash': 'hashed_pass',
            'language': 'en', 'is_active': True, 'is_verified': False, 'is_deleted': False,
            'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)
        }
        repo = UserRepository(mock_pool)
        with patch.object(repo, 'get_user_by_id', return_value=expected_result) as mock_get:
            result = await repo.get_user_by_id(1)
            mock_get.assert_called_once_with(1)
            assert result['id'] == 1

    async def test_update_user_success(self, mock_pool):
        repo = UserRepository(mock_pool)
        with patch.object(repo, 'update_user', return_value={'id': 1}) as mock_update:
            result = await repo.update_user(1, {'email': 'new@example.com'})
            mock_update.assert_called_once_with(1, {'email': 'new@example.com'})
            assert result['id'] == 1

    async def test_delete_user_success(self, mock_pool):
        repo = UserRepository(mock_pool)
        with patch.object(repo, 'delete_user', return_value=True) as mock_delete:
            result = await repo.delete_user(1)
            mock_delete.assert_called_once_with(1)
            assert result is True


@pytest.mark.anyio
class TestApiKeyRepository:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        return pool

    async def test_create_user_api_key_success(self, mock_pool):
        expected_result = {
            'id': 1, 'user_id': 1, 'key': 'hashed_key', 'limits': {'requests_per_day': 1000},
            'is_active': True, 'created_at': datetime.now(timezone.utc), 'expires_at': None
        }
        repo = ApiKeyRepository(mock_pool)
        with patch.object(repo, 'create_user_api_key', return_value=expected_result) as mock_create:
            result = await repo.create_user_api_key(1, 'hashed_key', {'requests_per_day': 1000})
            mock_create.assert_called_once_with(1, 'hashed_key', {'requests_per_day': 1000})
            assert result['user_id'] == 1

    async def test_get_user_api_keys_success(self, mock_pool):
        expected_result = [{
            'id': 1, 'key': 'hashed_key', 'limits': {'requests_per_day': 1000},
            'is_active': True, 'created_at': datetime.now(timezone.utc), 'expires_at': None
        }]
        repo = ApiKeyRepository(mock_pool)
        with patch.object(repo, 'get_user_api_keys', return_value=expected_result) as mock_get:
            result = await repo.get_user_api_keys(1)
            mock_get.assert_called_once_with(1)
            assert len(result) == 1

    async def test_get_user_api_key_by_key_success(self, mock_pool):
        expected_result = {
            'id': 1, 'user_id': 1, 'limits': {'requests_per_day': 1000},
            'is_active': True, 'created_at': datetime.now(timezone.utc), 'expires_at': None
        }
        repo = ApiKeyRepository(mock_pool)
        with patch.object(repo, 'get_user_api_key_by_key', return_value=expected_result) as mock_get:
            result = await repo.get_user_api_key_by_key('hashed_key')
            mock_get.assert_called_once_with('hashed_key')
            assert result['id'] == 1


@pytest.mark.anyio
class TestRSSFeedRepository:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        return pool

    async def test_create_user_rss_feed_success(self, mock_pool):
        expected_result = {
            'id': 1, 'url': 'http://example.com/rss', 'name': 'Test Feed',
            'category_id': 1, 'language': 'en', 'is_active': True,
            'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)
        }
        repo = RSSFeedRepository(mock_pool)
        with patch.object(repo, 'create_user_rss_feed', return_value=expected_result) as mock_create:
            result = await repo.create_user_rss_feed(1, 'http://example.com/rss', 'Test Feed', 1, 'en')
            mock_create.assert_called_once_with(1, 'http://example.com/rss', 'Test Feed', 1, 'en')
            assert result['name'] == 'Test Feed'

    async def test_get_user_rss_feeds_success(self, mock_pool):
        expected_result = [{
            'id': 1, 'url': 'http://example.com/rss', 'name': 'Test Feed',
            'category_id': 1, 'language': 'en', 'is_active': True,
            'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)
        }]
        repo = RSSFeedRepository(mock_pool)
        with patch.object(repo, 'get_user_rss_feeds', return_value=expected_result) as mock_get:
            result = await repo.get_user_rss_feeds(1, 10, 0)
            mock_get.assert_called_once_with(1, 10, 0)
            assert len(result) == 1


@pytest.mark.anyio
class TestCategoryRepository:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        return pool

    async def test_get_all_category_ids_success(self, mock_pool):
        repo = CategoryRepository(mock_pool)
        with patch.object(repo, 'get_all_category_ids', return_value=[1, 2, 3]) as mock_get:
            result = await repo.get_all_category_ids()
            mock_get.assert_called_once()
            assert result == [1, 2, 3]

    async def test_get_user_categories_success(self, mock_pool):
        expected_result = [{'id': 1, 'name': 'Tech'}, {'id': 2, 'name': 'Sports'}]
        repo = CategoryRepository(mock_pool)
        with patch.object(repo, 'get_user_categories', return_value=expected_result) as mock_get:
            result = await repo.get_user_categories(1, None)
            mock_get.assert_called_once_with(1, None)
            assert len(result) == 2


@pytest.mark.anyio
class TestSourceRepository:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        return pool

    async def test_get_source_id_by_alias_success(self, mock_pool):
        repo = SourceRepository(mock_pool)
        with patch.object(repo, 'get_source_id_by_alias', return_value=1) as mock_get:
            result = await repo.get_source_id_by_alias('bbc')
            mock_get.assert_called_once_with('bbc')
            assert result == 1


@pytest.mark.anyio
class TestRSSItemRepository:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        return pool

    async def test_get_recent_rss_items_for_broadcast_success(self, mock_pool):
        expected_result = [{'news_id': 'news1', 'original_title': 'Title', 'original_language': 'en', 'category_name': 'Tech', 'created_at': datetime.now(timezone.utc)}]
        repo = RSSItemRepository(mock_pool)
        with patch.object(repo, 'get_recent_rss_items_for_broadcast', return_value=expected_result) as mock_get:
            result = await repo.get_recent_rss_items_for_broadcast(datetime.now(timezone.utc) - timedelta(hours=1))
            assert len(result) == 1
            assert result[0]['news_id'] == 'news1'