# exceptions/database_exceptions.py - Database-related exceptions
from typing import Optional, Dict, Any
from .base_exceptions import FireFeedException


class DatabaseException(FireFeedException):
    """Base exception for database operations"""
    pass


class DatabaseConnectionError(DatabaseException):
    """Exception raised when database connection fails"""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Database connection failed", details)


class DatabaseQueryError(DatabaseException):
    """Exception raised when database query fails"""

    def __init__(self, query: str, error: str, details: Optional[Dict[str, Any]] = None):
        message = f"Database query failed: {error}"
        super().__init__(message, details)
        self.query = query
        self.error = error