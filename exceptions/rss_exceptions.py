# exceptions/rss_exceptions.py - RSS-related exceptions
from typing import Optional, Dict, Any
from .base_exceptions import FireFeedException


class RSSException(FireFeedException):
    """Base exception for RSS-related operations"""
    pass


class RSSFetchError(RSSException):
    """Exception raised when RSS feed cannot be fetched"""

    def __init__(self, url: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to fetch RSS feed from {url}"
        if status_code:
            message += f" (HTTP {status_code})"
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code


class RSSParseError(RSSException):
    """Exception raised when RSS feed cannot be parsed"""

    def __init__(self, url: str, parse_error: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to parse RSS feed from {url}"
        if parse_error:
            message += f": {parse_error}"
        super().__init__(message, details)
        self.url = url
        self.parse_error = parse_error


class RSSValidationError(RSSException):
    """Exception raised when RSS feed validation fails"""

    def __init__(self, url: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"RSS feed validation failed for {url}: {reason}"
        super().__init__(message, details)
        self.url = url
        self.reason = reason