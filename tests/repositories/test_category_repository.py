import pytest
from unittest.mock import AsyncMock
from repositories.category_repository import CategoryRepository


@pytest.fixture
def repo(mock_db_pool):
    return CategoryRepository(mock_db_pool)


class TestCategoryRepository:
    @pytest.mark.asyncio
    async def test_get_user_categories_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[(1, "Tech"), (2, "News")])

        result = await repo.get_user_categories(1)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Tech"

    @pytest.mark.asyncio
    async def test_get_user_categories_with_source_ids(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[(1, "Tech")])

        result = await repo.get_user_categories(1, [1, 2])

        assert len(result) == 1
        assert result[0]["name"] == "Tech"

    @pytest.mark.asyncio
    async def test_update_user_categories_success(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        # Mock the execute method
        cur.execute = AsyncMock()

        result = await repo.update_user_categories(1, [1, 2, 3])

        assert result is True
        cur.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_user_categories_failure(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock execute to fail on BEGIN but succeed on ROLLBACK
        def execute_side_effect(query, *args):
            if "BEGIN" in query:
                raise Exception("DB error")
            # Allow ROLLBACK and other commands to succeed
            return AsyncMock()
        
        cur.execute = AsyncMock(side_effect=execute_side_effect)

        result = await repo.update_user_categories(1, [1, 2])

        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_category_ids(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[(1,), (2,), (3,)])

        result = await repo.get_all_category_ids()

        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_get_category_id_by_name_found(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        cur.fetchone.return_value = (1,)

        result = await repo.get_category_id_by_name("Tech")

        assert result == 1

    @pytest.mark.asyncio
    async def test_get_category_id_by_name_not_found(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        cur.fetchone.return_value = None

        result = await repo.get_category_id_by_name("NonExistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_categories_list(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        cur.fetchall.return_value = [(1, "Tech", 5), (2, "News", 3)]
        cur.fetchone.return_value = (2,)

        total, categories = await repo.get_all_categories_list(10, 0)

        assert total == 2
        assert len(categories) == 2
        assert categories[0]["name"] == "Tech"
        assert categories[0]["feeds_count"] == 5