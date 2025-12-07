# telegram_bot/utils/validation_utils.py - Validation utilities
import logging
import aiohttp

logger = logging.getLogger(__name__)


async def validate_image_url(image_url: str) -> bool:
    """Checks availability and correctness of image URL."""
    if not image_url:
        return False

    try:
        # Make HEAD request to check availability
        timeout = aiohttp.ClientTimeout(total=5, connect=2)
        async with aiohttp.ClientSession() as session:
            async with session.head(image_url, timeout=timeout) as response:
                if response.status != 200:
                    logger.debug(f"Image unavailable (status {response.status}): {image_url}")
                    return False

                # Check Content-Type
                content_type = response.headers.get('Content-Type', '').lower()
                if not content_type.startswith('image/'):
                    logger.debug(f"Incorrect Content-Type '{content_type}' for: {image_url}")
                    return False

                # Check size (if specified)
                content_length = response.headers.get('Content-Length')
                if content_length:
                    try:
                        size = int(content_length)
                        if size > 10 * 1024 * 1024:  # 10 MB limit
                            logger.debug(f"Image too large ({size} bytes): {image_url}")
                            return False
                    except (ValueError, TypeError):
                        pass

                return True

    except asyncio.TimeoutError:
        logger.debug(f"Timeout checking image: {image_url}")
        return False
    except Exception as e:
        logger.debug(f"Error checking image {image_url}: {e}")
        return False