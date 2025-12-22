import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from apps.api.middleware import (
    ApplicationRateLimitMiddleware,
    ForceUTF8ResponseMiddleware,
    setup_middleware,
    limiter
)
from slowapi.errors import RateLimitExceeded


class TestApplicationRateLimitMiddleware:
    """Test the application-level rate limiting middleware"""
    
    @pytest.mark.asyncio
    async def test_dispatch_auth_endpoint(self):
        """Test that auth endpoints are handled correctly"""
        middleware = ApplicationRateLimitMiddleware(app=MagicMock())
        
        # Mock request for auth endpoint
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/auth/login"
        
        # Mock the call_next function
        mock_call_next = AsyncMock()
        mock_response = MagicMock()
        mock_call_next.return_value = mock_response
        
        # Mock get_remote_address
        with patch('apps.api.middleware.get_remote_address', return_value='127.0.0.1'):
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify the response is returned
            assert response == mock_response
            mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_general_api_endpoint(self):
        """Test that general API endpoints are handled correctly"""
        middleware = ApplicationRateLimitMiddleware(app=MagicMock())
        
        # Mock request for general API endpoint
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/users/me"
        
        # Mock the call_next function
        mock_call_next = AsyncMock()
        mock_response = MagicMock()
        mock_call_next.return_value = mock_response
        
        # Mock get_remote_address
        with patch('apps.api.middleware.get_remote_address', return_value='127.0.0.1'):
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify the response is returned
            assert response == mock_response
            mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_other_endpoint(self):
        """Test that other endpoints are handled correctly"""
        middleware = ApplicationRateLimitMiddleware(app=MagicMock())
        
        # Mock request for non-API endpoint
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/docs"
        
        # Mock the call_next function
        mock_call_next = AsyncMock()
        mock_response = MagicMock()
        mock_call_next.return_value = mock_response
        
        # Mock get_remote_address
        with patch('apps.api.middleware.get_remote_address', return_value='127.0.0.1'):
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify the response is returned
            assert response == mock_response
            mock_call_next.assert_called_once_with(mock_request)


class TestForceUTF8ResponseMiddleware:
    """Test the UTF-8 response middleware"""
    
    @pytest.mark.asyncio
    async def test_dispatch_json_response_no_charset(self):
        """Test JSON response without charset gets UTF-8 added"""
        middleware = ForceUTF8ResponseMiddleware(app=MagicMock())
        
        # Mock request
        mock_request = MagicMock()
        
        # Mock response with JSON content type but no charset
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        
        # Mock call_next to return the response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify charset was added
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_json_response_with_different_charset(self):
        """Test JSON response with different charset gets replaced with UTF-8"""
        middleware = ForceUTF8ResponseMiddleware(app=MagicMock())
        
        # Mock request
        mock_request = MagicMock()
        
        # Mock response with JSON content type and different charset
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json; charset=iso-8859-1"}
        
        # Mock call_next to return the response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify charset was replaced
        assert response.headers["content-type"] == "application/json;charset=utf-8"
        mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_json_response_with_utf8_charset(self):
        """Test JSON response with UTF-8 charset is not modified"""
        middleware = ForceUTF8ResponseMiddleware(app=MagicMock())
        
        # Mock request
        mock_request = MagicMock()
        
        # Mock response with JSON content type and UTF-8 charset
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json; charset=utf-8"}
        
        # Mock call_next to return the response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify charset was not modified
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_text_response_no_charset(self):
        """Test text response without charset gets UTF-8 added"""
        middleware = ForceUTF8ResponseMiddleware(app=MagicMock())
        
        # Mock request
        mock_request = MagicMock()
        
        # Mock response with text content type but no charset
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        
        # Mock call_next to return the response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify charset was added
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_text_response_with_different_charset(self):
        """Test text response with different charset gets replaced with UTF-8"""
        middleware = ForceUTF8ResponseMiddleware(app=MagicMock())
        
        # Mock request
        mock_request = MagicMock()
        
        # Mock response with text content type and different charset
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html; charset=iso-8859-1"}
        
        # Mock call_next to return the response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify charset was replaced
        assert response.headers["content-type"] == "text/html;charset=utf-8"
        mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_other_content_type_unchanged(self):
        """Test that non-text/non-JSON content types are not modified"""
        middleware = ForceUTF8ResponseMiddleware(app=MagicMock())
        
        # Mock request
        mock_request = MagicMock()
        
        # Mock response with other content type
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "image/png"}
        
        # Mock call_next to return the response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify content type was not modified
        assert response.headers["content-type"] == "image/png"
        mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_dispatch_exception_handling(self):
        """Test that exceptions in middleware are logged"""
        middleware = ForceUTF8ResponseMiddleware(app=MagicMock())
        
        # Mock request
        mock_request = MagicMock()
        
        # Mock call_next to raise an exception
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = Exception("Test error")
        
        # Mock logger
        with patch('apps.api.middleware.logger') as mock_logger:
            with pytest.raises(Exception, match="Test error"):
                await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify error was logged
            mock_logger.error.assert_called_once_with("[Middleware Error] ForceUTF8: Test error")


class TestSetupMiddleware:
    """Test the middleware setup function"""
    
    def test_setup_middleware(self):
        """Test that setup_middleware adds all required middleware and handlers"""
        app = FastAPI()
        
        # Call setup_middleware
        setup_middleware(app)
        
        # Verify middleware were added
        middleware_classes = [middleware.cls for middleware in app.user_middleware]
        
        # Check that ForceUTF8ResponseMiddleware was added
        assert ForceUTF8ResponseMiddleware in middleware_classes
        
        # Check that ApplicationRateLimitMiddleware was added
        assert ApplicationRateLimitMiddleware in middleware_classes
        
        # Check that SlowAPIMiddleware was added
        from slowapi.middleware import SlowAPIMiddleware
        assert SlowAPIMiddleware in middleware_classes
        
        # Verify exception handler was added
        assert RateLimitExceeded in app.exception_handlers
        
        # Verify limiter is in app state
        assert hasattr(app.state, 'limiter')
        assert app.state.limiter == limiter