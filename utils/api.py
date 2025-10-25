from typing import List, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel):
    """Базовый класс для стандартизации API ответов"""

    @staticmethod
    def paginated_response(count: int, results: List) -> dict:
        """Форматирует ответ с пагинацией"""
        return {"count": count, "results": results}

    @staticmethod
    def single_item_response(item) -> dict:
        """Форматирует ответ с одним элементом"""
        return {"result": item}

    @staticmethod
    def success_response(message: str = "Success") -> dict:
        """Форматирует успешный ответ"""
        return {"message": message}

    @staticmethod
    def error_response(message: str, status_code: int = 400) -> dict:
        """Форматирует ответ с ошибкой"""
        return {"error": message, "status_code": status_code}


class PaginatedResponse(BaseModel, Generic[T]):
    """Стандартизированная модель для пагинированных ответов"""

    count: int
    results: List[T]
