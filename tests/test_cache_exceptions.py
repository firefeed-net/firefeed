import pytest
from exceptions.cache_exceptions import CacheException, CacheConnectionError


class TestCacheException:
    """Test the CacheException base class"""
    
    def test_cache_exception_no_details(self):
        """Test CacheException with no details"""
        message = "Cache operation failed"
        exception = CacheException(message)
        
        assert str(exception) == "Cache operation failed"
        assert exception.message == "Cache operation failed"
        assert exception.details == {}
    
    def test_cache_exception_with_details(self):
        """Test CacheException with details"""
        message = "Cache operation failed"
        details = {"operation": "get", "key": "test_key"}
        exception = CacheException(message, details)
        
        assert str(exception) == "Cache operation failed"
        assert exception.message == "Cache operation failed"
        assert exception.details == {"operation": "get", "key": "test_key"}


class TestCacheConnectionError:
    """Test the CacheConnectionError exception"""
    
    def test_cache_connection_error_no_details(self):
        """Test CacheConnectionError with no details"""
        cache_type = "redis"
        exception = CacheConnectionError(cache_type)
        
        assert str(exception) == "Cache connection failed for redis"
        assert exception.message == "Cache connection failed for redis"
        assert exception.cache_type == "redis"
        assert exception.details == {}
    
    def test_cache_connection_error_with_details(self):
        """Test CacheConnectionError with details"""
        cache_type = "memcached"
        details = {"host": "localhost", "port": 11211}
        exception = CacheConnectionError(cache_type, details)
        
        assert str(exception) == "Cache connection failed for memcached"
        assert exception.message == "Cache connection failed for memcached"
        assert exception.cache_type == "memcached"
        assert exception.details == {"host": "localhost", "port": 11211}
    
    def test_cache_connection_error_inheritance(self):
        """Test that CacheConnectionError inherits from CacheException"""
        cache_type = "redis"
        exception = CacheConnectionError(cache_type)
        
        assert isinstance(exception, CacheException)
        assert isinstance(exception, Exception)