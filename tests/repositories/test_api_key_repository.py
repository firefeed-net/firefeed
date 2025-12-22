import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from repositories.api_key_repository import ApiKeyRepository
from exceptions import DatabaseException


@pytest.fixture
def repo(mock_db_pool):
    return ApiKeyRepository(mock_db_pool)


class TestApiKeyRepository:
    @pytest.mark.asyncio
    async def test_create_user_api_key_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value  # Get the connection from the context manager
        cur = conn.cursor_mock  # Use the cursor mock directly
        
        cur.fetchone.return_value = (1, 1, {"requests_per_day": 1000}, True, datetime.now(timezone.utc), None)

        result = await repo.create_user_api_key(1, "test_key", {"requests_per_day": 1000})

        assert result["id"] == 1
        assert result["user_id"] == 1
        cur.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_api_key_failure(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.execute.side_effect = Exception("DB error")

        with pytest.raises(DatabaseException):
            await repo.create_user_api_key(1, "test_key", {"requests_per_day": 1000})

    @pytest.mark.asyncio
    async def test_get_user_api_keys_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Create test data
        test_rows = [
            (1, "key1", {"requests_per_day": 1000}, True, datetime.now(timezone.utc), None),
            (2, "key2", {"requests_per_day": 500}, False, datetime.now(timezone.utc), None)
        ]
        
        # Make fetchall return our test data
        cur.fetchall = AsyncMock(return_value=test_rows)

        result = await repo.get_user_api_keys(1)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_get_user_api_key_by_id_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchone.return_value = (1, 1, {"requests_per_day": 1000}, True, datetime.now(timezone.utc), None)

        result = await repo.get_user_api_key_by_id(1, 1)

        assert result["id"] == 1
        assert result["user_id"] == 1

    @pytest.mark.asyncio
    async def test_get_user_api_key_by_id_not_found(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchone.return_value = None

        result = await repo.get_user_api_key_by_id(1, 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_api_key_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchone.return_value = (1, 1, {"requests_per_day": 2000}, False, datetime.now(timezone.utc), None)

        result = await repo.update_user_api_key(1, 1, {"is_active": False, "limits": {"requests_per_day": 2000}})

        assert result["is_active"] is False
        assert result["limits"]["requests_per_day"] == 2000

    @pytest.mark.asyncio
    async def test_delete_user_api_key_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.rowcount = 1

        result = await repo.delete_user_api_key(1, 1)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_api_key_by_key_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchone.return_value = (1, 1, {"requests_per_day": 1000}, True, datetime.now(timezone.utc), None)

        result = await repo.get_user_api_key_by_key("test_key")

        assert result["id"] == 1
        assert result["user_id"] == 1