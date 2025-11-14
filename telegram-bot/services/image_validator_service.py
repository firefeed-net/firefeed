import aiohttp
import logging
from typing import Optional

from ..interfaces.image_validator_interface import IImageValidatorService

logger = logging.getLogger(__name__)


class ImageValidatorService(IImageValidatorService):
    """Service for validating image URLs."""

    async def validate_image_url(self, image_url: str) -> bool:
        """Validates the availability and correctness of an image URL."""
        if not image_url:
            return False

        try:
            # Get HTTP session from global (will be injected)
            # For now, assume it's passed or use a simple session
            # In DI, we'll inject the session
            # Since this is a service, we'll need to inject http_session
            # But for simplicity, create a local session or assume it's available
            # Actually, since it's async, we can create a session here, but better to inject

            # For now, implement with local session, but in real DI, inject it
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

        except aiohttp.ClientTimeout:
            logger.debug(f"Timeout checking image: {image_url}")
            return False
        except Exception as e:
            logger.debug(f"Error checking image {image_url}: {e}")
            return False