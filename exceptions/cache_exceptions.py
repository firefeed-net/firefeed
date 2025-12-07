# exceptions/cache_exceptions.py - Cache-related exceptions
from typing import Optional, Dict, Any
from exceptions.base_exceptions import FireFeedException


class CacheException(FireFeedException):
    """Base exception for caching operations"""
    pass


class CacheConnectionError(CacheException):
    """Exception raised when cache connection fails"""

    def __init__(self, cache_type: str, details: Optional[Dict[str, Any]] = None):
        message = f"Cache connection failed for {cache_type}"
        super().__init__(message, details)
        self.cache_type = cache_type