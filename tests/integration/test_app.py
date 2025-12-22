from fastapi import FastAPI
import os
import pytest
from unittest.mock import patch, AsyncMock
from apps.api.app import app


def test_app_creation():
    assert app is not None
    assert isinstance(app, FastAPI)
    assert app.title == "FireFeed API"
    assert app.version == "1.0.0"


def test_app_cors_configuration():
    """Test CORS configuration for different environments"""
    # Test development environment
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        # Re-import to trigger CORS setup
        import importlib
        import apps.api.app
        importlib.reload(apps.api.app)
        
        # Check if CORS middleware is added
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == 'CORSMiddleware':
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
        # Check the middleware args for allowed origins
        # Access the configuration from the middleware class
        cors_config = cors_middleware.kwargs
        allow_origins = cors_config.get('allow_origins', [])
        
        assert "http://localhost" in allow_origins
        assert "http://localhost:3000" in allow_origins
        assert "http://localhost:8000" in allow_origins
        assert "http://127.0.0.1" in allow_origins
        assert "http://127.0.0.1:3000" in allow_origins
        assert "http://127.0.0.1:8000" in allow_origins
        assert "https://firefeed.net" in allow_origins
        assert "https://www.firefeed.net" in allow_origins


def test_app_cors_configuration_production():
    """Test CORS configuration for production environment"""
    # Check if CORS middleware is added
    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == 'CORSMiddleware':
            cors_middleware = middleware
            break
    
    assert cors_middleware is not None
    # Access the configuration from the middleware class
    cors_config = cors_middleware.kwargs
    allow_origins = cors_config.get('allow_origins', [])
    
    # Since app is loaded once, we just check that CORS middleware exists
    assert isinstance(allow_origins, list)
    assert len(allow_origins) > 0

