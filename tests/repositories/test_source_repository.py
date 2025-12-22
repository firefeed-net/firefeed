import pytest
from unittest.mock import AsyncMock
from repositories.source_repository import SourceRepository


@pytest.fixture
def repo(mock_db_pool):
    return SourceRepository(mock_db_pool)


class TestSourceRepository:
    @pytest.mark.asyncio
    async def test_get_source_id_by_alias_found(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchone.return_value = (1,)

        result = await repo.get_source_id_by_alias("bbc")

        assert result == 1

    @pytest.mark.asyncio
    async def test_get_source_id_by_alias_not_found(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchone.return_value = None

        result = await repo.get_source_id_by_alias("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_sources_list(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchall.return_value = [(1, "BBC News", "bbc", 10), (2, "CNN", "cnn", 5)]
        cur.fetchone.return_value = (2,)

        total, sources = await repo.get_all_sources_list(10, 0)

        assert total == 2
        assert len(sources) == 2
        assert sources[0]["name"] == "BBC News"
        assert sources[0]["alias"] == "bbc"
        assert sources[0]["feeds_count"] == 10

    @pytest.mark.asyncio
    async def test_get_all_sources_list_with_category_ids(self, repo, mock_db_pool):
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchall.return_value = [(1, "Tech Source", "tech", 3)]
        cur.fetchone.return_value = (1,)

        total, sources = await repo.get_all_sources_list(10, 0, [1, 2])

        assert total == 1
        assert len(sources) == 1
        assert sources[0]["alias"] == "tech"