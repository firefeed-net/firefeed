# interfaces/core_interfaces.py - Core system interfaces
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class ILogger(ABC):
    """Interface for logging operations"""

    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def critical(self, message: str, *args, **kwargs) -> None:
        pass


class IDatabasePool(ABC):
    """Interface for database connection pool"""

    @abstractmethod
    async def acquire(self):
        """Acquire database connection"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close pool"""
        pass


class IMaintenanceService(ABC):
    """Interface for maintenance operations"""

    @abstractmethod
    async def cleanup_duplicates(self) -> None:
        """Clean up duplicate RSS items"""
        pass


class IDuplicateDetector(ABC):
    """Interface for duplicate content detection"""

    @abstractmethod
    async def is_duplicate(self, title: str, content: str, link: str, lang: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if content is duplicate"""
        pass

    @abstractmethod
    async def process_rss_item(self, rss_item_id: str, title: str, content: str, lang_code: str) -> bool:
        """Process RSS item for duplicate detection and embedding generation"""
        pass