import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from apps.api.app import app


class AsyncContextManagerMock:
    """A mock that can be used both as a coroutine and as an async context manager"""
    def __init__(self, return_value):
        self.return_value = return_value
        self._coroutine = None
    
    def __await__(self):
        """Make this object awaitable"""
        if self._coroutine is None:
            async def _coroutine():
                return self.return_value
            self._coroutine = _coroutine()
        return self._coroutine.__await__()
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None
    
    def __aiter__(self):
        """Support async iteration"""
        return self.return_value
    
    async def __anext__(self):
        """Support async iteration"""
        if hasattr(self.return_value, '__anext__'):
            return await self.return_value.__anext__()
        raise StopAsyncIteration


class AsyncConnectionMock:
    """Mock connection that supports async context manager and cursor"""
    def __init__(self, cursor_mock=None):
        self.cursor_mock = cursor_mock or AsyncMock()
    
    def cursor(self):
        """Return cursor as async context manager"""
        return AsyncContextManagerMock(self.cursor_mock)


@pytest.fixture
def mock_db_pool():
    """Create a properly mocked database pool"""
    pool = AsyncMock()
    conn = AsyncConnectionMock()
    cur = AsyncMock()
    
    # Set up the connection's cursor to return our mock cursor
    conn.cursor_mock = cur
    
    # Make pool.acquire return an async context manager that yields the connection
    pool.acquire = MagicMock(return_value=AsyncContextManagerMock(conn))
    
    return pool


@pytest.fixture
def mock_cursor():
    """Create a mock database cursor"""
    return AsyncMock()


@pytest.fixture
def mock_conn():
    """Create a mock database connection"""
    return AsyncConnectionMock()


@pytest.fixture
def mock_cur():
    """Create a mock database cursor"""
    return AsyncMock()


@pytest.fixture
def client():
    """Create a test client for FastAPI app"""
    return TestClient(app)