from tenacity import retry, stop_after_attempt, wait_exponential


def retry_on_failure(max_attempts: int = 5, multiplier: int = 1, min_wait: int = 2, max_wait: int = 30):
    """Retry decorator for functions that may fail."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait)
    )