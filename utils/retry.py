import logging
from functools import wraps
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def retry_operation(max_attempts: int = 5, backoff_multiplier: float = 1.0, max_backoff: float = 30.0) -> Callable:
    """
    Decorator for retrying asynchronous operations

    Args:
        max_attempts: Maximum number of attempts
        backoff_multiplier: Multiplier for exponential backoff
        max_backoff: Maximum delay between attempts

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=backoff_multiplier, min=2, max=max_backoff),
            reraise=True,
        )
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"[RETRY] Attempt to execute {func.__name__} failed: {e}")
                raise  # Throw exception for tenacity

        return wrapper

    return decorator


# Ready-made decorators for typical cases
retry_db_operation = retry_operation(max_attempts=3, backoff_multiplier=0.5, max_backoff=10.0)
retry_api_call = retry_operation(max_attempts=5, backoff_multiplier=1.0, max_backoff=30.0)
retry_file_operation = retry_operation(max_attempts=3, backoff_multiplier=0.1, max_backoff=5.0)
