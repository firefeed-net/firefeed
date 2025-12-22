import pytest
from unittest.mock import AsyncMock, MagicMock
from services.database_pool_adapter import DatabasePoolAdapter


@pytest.fixture
def mock_db_pool():
    return AsyncMock()


@pytest.fixture
def adapter(mock_db_pool):
    return DatabasePoolAdapter(mock_db_pool)


class TestDatabasePoolAdapter:
    @pytest.mark.asyncio
    async def test_close(self, adapter):
        # close method does nothing, just ensure it doesn't raise
        await adapter.close()