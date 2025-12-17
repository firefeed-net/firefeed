# services/translation/model_manager.py
import asyncio
import logging
import time
from typing import Dict, Any, Tuple, Optional
from interfaces import IModelManager
from config.services_config import get_service_config
from exceptions import TranslationModelError

logger = logging.getLogger(__name__)


class CachedModel:
    """Class for storing model with metadata"""
    def __init__(self, model, tokenizer, timestamp):
        self.model = model
        self.tokenizer = tokenizer
        self.timestamp = timestamp
        self.last_used = timestamp


class ModelManager(IModelManager):
    """Service for managing ML translation models"""

    def __init__(self, device: str = "cpu", max_cached_models: int = 5, model_cleanup_interval: int = 1800):
        self.device = device
        self.max_cached_models = max_cached_models
        self.model_cleanup_interval = model_cleanup_interval
        self.model_cache: Dict[str, CachedModel] = {}
        self.model_load_lock = asyncio.Lock()

        # Start cleanup task
        asyncio.create_task(self._model_cleanup_task())

    async def get_model(self, source_lang: str, target_lang: str) -> Tuple[Any, Any]:
        """Get model and tokenizer for translation direction"""
        direction = f"{source_lang}_{target_lang}"
        cache_key = f"translation_{direction}"

        # Check cache first
        if cache_key in self.model_cache:
            cached = self.model_cache[cache_key]
            cached.last_used = time.time()
            logger.debug(f"[MODEL] Using cached model for {direction}")
            return cached.model, cached.tokenizer

        # Load model
        async with self.model_load_lock:
            # Double-check cache after acquiring lock
            if cache_key in self.model_cache:
                cached = self.model_cache[cache_key]
                cached.last_used = time.time()
                return cached.model, cached.tokenizer

            try:
                logger.info(f"[MODEL] Loading model for {direction}")

                # Import here to avoid circular imports and conditional loading
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

                # Use the configured translation model
                config = get_service_config()
                model_name = config.translation.models.translation_model

                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)

                # Cache the model
                current_time = time.time()
                self.model_cache[cache_key] = CachedModel(model, tokenizer, current_time)

                # Enforce cache limit
                await self._enforce_cache_limit()

                logger.info(f"[MODEL] Model loaded and cached for {direction}")
                return model, tokenizer

            except Exception as e:
                raise TranslationModelError(
                    model_name=model_name,
                    error=f"Failed to load model for {direction}: {str(e)}"
                )

    async def preload_popular_models(self) -> None:
        """Preload commonly used models"""
        popular_directions = [
            ("en", "ru"),
            ("ru", "en"),
            ("de", "en"),
            ("fr", "en")
        ]

        logger.info("[MODEL] Preloading popular models...")
        tasks = []
        for source_lang, target_lang in popular_directions:
            tasks.append(self.get_model(source_lang, target_lang))

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("[MODEL] Popular models preloaded")
        except Exception as e:
            logger.error(f"[MODEL] Error preloading models: {e}")
            raise TranslationModelError(
                model_name="multiple",
                error=f"Failed to preload popular models: {str(e)}"
            )

    def clear_cache(self) -> None:
        """Clear all cached models"""
        logger.info(f"[MODEL] Clearing cache ({len(self.model_cache)} models)")
        self.model_cache.clear()

    async def unload_unused_models(self, max_age_seconds: int = 3600) -> int:
        """Unload models that haven't been used recently"""
        current_time = time.time()
        models_to_remove = []

        for direction, cached in self.model_cache.items():
            if current_time - cached.last_used > max_age_seconds:
                models_to_remove.append(direction)

        for direction in models_to_remove:
            logger.info(f"[MODEL] Unloading unused model for {direction}")
            del self.model_cache[direction]

        logger.info(f"[MODEL] Unloaded {len(models_to_remove)} unused models")
        return len(models_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get model cache statistics"""
        total_models = len(self.model_cache)
        cache_size_mb = 0

        for cached in self.model_cache.values():
            # Rough estimation - each model is ~500MB
            cache_size_mb += 500

        return {
            "total_cached_models": total_models,
            "estimated_cache_size_mb": cache_size_mb,
            "cached_directions": list(self.model_cache.keys())
        }

    async def _enforce_cache_limit(self) -> None:
        """Enforce maximum cache size by removing least recently used models"""
        if len(self.model_cache) <= self.max_cached_models:
            return

        # Sort by last_used time (oldest first)
        sorted_cache = sorted(self.model_cache.items(), key=lambda x: x[1].last_used)

        # Remove oldest models
        models_to_remove = len(self.model_cache) - self.max_cached_models
        for i in range(models_to_remove):
            direction, cached = sorted_cache[i]
            logger.info(f"[MODEL] Removing cached model for {direction}")
            del self.model_cache[direction]

    async def _model_cleanup_task(self) -> None:
        """Background task to cleanup old unused models"""
        while True:
            try:
                await asyncio.sleep(self.model_cleanup_interval)
                await self._cleanup_old_models()
            except Exception as e:
                logger.error(f"[MODEL] Error in cleanup task: {e}")
                raise TranslationModelError(
                    model_name="system",
                    error=f"Model cleanup task failed: {str(e)}"
                )

    async def _cleanup_old_models(self) -> None:
        """Remove models that haven't been used for too long"""
        current_time = time.time()
        max_age = self.model_cleanup_interval * 2  # 2 cleanup intervals

        models_to_remove = []
        for direction, cached in self.model_cache.items():
            if current_time - cached.last_used > max_age:
                models_to_remove.append(direction)

        for direction in models_to_remove:
            logger.info(f"[MODEL] Removing old unused model for {direction}")
            del self.model_cache[direction]