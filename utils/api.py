from typing import List, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel):
    """Base class for standardizing API responses"""

    @staticmethod
    def paginated_response(count: int, results: List) -> dict:
        """Formats a paginated response"""
        return {"count": count, "results": results}

    @staticmethod
    def single_item_response(item) -> dict:
        """Formats a response with a single item"""
        return {"result": item}

    @staticmethod
    def success_response(message: str = "Success") -> dict:
        """Formats a success response"""
        return {"message": message}

    @staticmethod
    def error_response(message: str, status_code: int = 400) -> dict:
        """Formats an error response"""
        return {"error": message, "status_code": status_code}


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized model for paginated responses"""

    count: int
    results: List[T]
