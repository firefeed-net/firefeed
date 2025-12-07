# exceptions/base_exceptions.py - Base exceptions
from typing import Optional, Dict, Any


class FireFeedException(Exception):
    """Base exception for FireFeed services"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}