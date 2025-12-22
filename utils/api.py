import httpx
from typing import List, TypeVar, Generic, Optional, Dict, Any
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


def make_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[str] = None,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Make an HTTP request and return a standardized response.

    Args:
        url: The URL to request
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers
        data: Optional data to send
        timeout: Optional timeout in seconds

    Returns:
        Dict with status_code and data or error
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.request(method, url, headers=headers, data=data)
            response.raise_for_status()
            return {"status_code": response.status_code, "data": response.json()}
    except httpx.HTTPStatusError as e:
        return {"status_code": e.response.status_code, "error": str(e)}
    except Exception as e:
        return {"status_code": 500, "error": str(e)}
