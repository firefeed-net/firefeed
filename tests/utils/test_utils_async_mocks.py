#!/usr/bin/env python3
"""
Simplified async mock utilities for testing.

This module provides simple, reliable async mock utilities that work correctly
with both sync and async context managers. It replaces the complex, error-prone
mock implementations with a clean, maintainable solution.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock


class AsyncContextManagerMock:
    """A simple async context manager mock that works reliably"""
    
    def __init__(self, return_value=None):
        self.return_value = return_value or self
        self.enter_called = False
        self.exit_called = False
    
    async def __aenter__(self):
        self.enter_called = True
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exit_called = True
        return False
    
    def __enter__(self):
        self.enter_called = True
        return self.return_value
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit_called = True
        return False


def create_httpx_client_mock():
    """Create a properly configured httpx client mock"""
    mock_client = AsyncContextManagerMock()
    mock_response = MagicMock()
    
    # Configure the client to return the response
    mock_client.request = MagicMock(return_value=mock_response)
    
    # Configure the response
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.text = ""
    mock_response.raise_for_status = MagicMock()
    
    return mock_client, mock_response


def create_aiohttp_session_mock():
    """Create a properly configured aiohttp session mock"""
    mock_session = MagicMock()
    mock_response = MagicMock()
    
    # Create a proper async context manager
    class AsyncResponseContextManager:
        def __init__(self, response):
            self.response = response
        
        async def __aenter__(self):
            return self.response
        
        async def __aexit__(self, *args):
            return False
    
    # Configure the session's get method to return the context manager
    async def mock_get(*args, **kwargs):
        return AsyncResponseContextManager(mock_response)
    
    mock_session.get = mock_get
    
    # Configure the response
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "image/jpeg"}
    mock_response.read = AsyncMock(return_value=b"fake image content")
    mock_response.text = AsyncMock(return_value="")
    mock_response.json = AsyncMock(return_value={})
    mock_response.raise_for_status = MagicMock()
    
    return mock_session, mock_response


def create_database_pool_mock():
    """Create a properly configured database pool mock"""
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Create proper async context managers
    class AsyncConnectionContextManager:
        def __init__(self, conn):
            self.conn = conn
        
        async def __aenter__(self):
            return self.conn
        
        async def __aexit__(self, *args):
            return False
    
    class AsyncCursorContextManager:
        def __init__(self, cursor, conn):
            self.cursor = cursor
            self.conn = conn
        
        async def __aenter__(self):
            return self.cursor
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Call commit when the cursor context manager exits successfully
            if exc_type is None:  # No exception occurred
                self.conn.commit()
            return False
    
    # Configure the pool's acquire method to return the connection context manager
    mock_pool.acquire = MagicMock(return_value=AsyncConnectionContextManager(mock_conn))
    
    # Configure the connection's cursor method to return the cursor context manager
    mock_conn.cursor = MagicMock(return_value=AsyncCursorContextManager(mock_cursor, mock_conn))
    
    # Configure cursor methods
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.rowcount = 0
    
    # Configure connection methods
    mock_conn.commit = MagicMock()
    mock_conn.rollback = MagicMock()
    
    return mock_pool, mock_conn, mock_cursor


def create_aiofiles_mock():
    """Create a properly configured aiofiles mock"""
    mock_file = AsyncContextManagerMock()
    
    # Configure the file mock
    mock_file.write = AsyncMock()
    mock_file.read = AsyncMock(return_value=b"")
    mock_file.close = AsyncMock()
    
    return mock_file


def create_simple_async_mock():
    """Create a simple async mock that works for basic scenarios"""
    return AsyncMock()


# Legacy compatibility - these functions now delegate to the simplified versions
def create_simple_aiohttp_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_async_context_manager_mock():
    """Legacy function - now uses the AsyncContextManagerMock class"""
    return AsyncContextManagerMock()


def create_aiohttp_session_with_context_manager_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_aiohttp_session_with_proper_context_manager_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_aiohttp_session_with_full_context_manager_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_aiohttp_session_with_full_async_context_manager_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_aiohttp_session_with_proper_async_context_manager_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_aiohttp_session_with_complete_async_context_manager_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_aiohttp_session_with_full_async_context_manager_mock_v2():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_aiohttp_session_mock_with_proper_coroutine_behavior():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()


def create_comprehensive_aiohttp_session_mock():
    """Legacy function - now uses the simplified aiohttp mock"""
    return create_aiohttp_session_mock()