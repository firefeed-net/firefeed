from abc import ABC, abstractmethod


class IImageValidatorService(ABC):
    @abstractmethod
    async def validate_image_url(self, image_url: str) -> bool:
        """Validates the availability and correctness of an image URL."""
        pass