# interfaces/translation_interfaces.py - Translation service interfaces
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class IModelManager(ABC):
    """Interface for ML model management"""

    @abstractmethod
    async def get_model(self, source_lang: str, target_lang: str) -> Tuple[Any, Any]:
        """Get model and tokenizer for translation direction"""
        pass

    @abstractmethod
    async def preload_popular_models(self) -> None:
        """Preload commonly used models"""
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear model cache"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get model cache statistics"""
        pass


class ITranslationService(ABC):
    """Interface for text translation operations"""

    @abstractmethod
    async def translate_async(self, texts: List[str], source_lang: str, target_lang: str,
                            context_window: int = 2, beam_size: Optional[int] = None) -> List[str]:
        """Translate texts asynchronously"""
        pass

    @abstractmethod
    async def prepare_translations(self, title: str, content: str, original_lang: str,
                                  target_langs: List[str]) -> Dict[str, Dict[str, str]]:
        """Prepare translations for title and content to multiple languages"""
        pass


class ITranslationCache(ABC):
    """Interface for translation caching"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached translation"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> None:
        """Set cached translation with TTL"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached translations"""
        pass


class ITranslatorQueue(ABC):
    """Interface for translation task queue"""

    @abstractmethod
    async def add_task(self, title: str, content: str, original_lang: str,
                      callback=None, error_callback=None, task_id=None) -> None:
        """Add translation task to queue"""
        pass

    @abstractmethod
    async def wait_completion(self) -> None:
        """Wait for all tasks to complete"""
        pass

    @abstractmethod
    def print_stats(self) -> None:
        """Print queue statistics"""
        pass