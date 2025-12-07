import logging
import spacy
from typing import Optional, Dict, Any
from config.services_config import get_service_config

logger = logging.getLogger(__name__)


class SpacyModelCache:
    """LRU cache for spaCy models"""

    def __init__(self, max_cache_size: int = 3):
        self.max_cache_size = max_cache_size
        self.models: Dict[str, Any] = {}
        self.usage_order: list = []  # LRU: last used at the end

    def get_model(self, lang_code: str) -> Optional[Any]:
        """
        Gets spaCy model for language with LRU caching

        Args:
            lang_code: Language code ('en', 'ru', 'de', 'fr')

        Returns:
            spaCy model or None if not found
        """
        if lang_code in self.models:
            # Update usage order (LRU)
            if lang_code in self.usage_order:
                self.usage_order.remove(lang_code)
            self.usage_order.append(lang_code)
            return self.models[lang_code]

        # Mapping language code to spacy model
        config = get_service_config()
        spacy_model_map = {
            "en": config.deduplication.spacy_models.en_model,
            "ru": config.deduplication.spacy_models.ru_model,
            "de": config.deduplication.spacy_models.de_model,
            "fr": config.deduplication.spacy_models.fr_model,
        }

        model_name = spacy_model_map.get(lang_code)
        if not model_name:
            logger.warning(f"[CACHE] Language model for '{lang_code}' not found, using 'en_core_web_sm'")
            model_name = "en_core_web_sm"

        try:
            # Load model
            nlp = spacy.load(model_name)
            self.models[lang_code] = nlp
            self.usage_order.append(lang_code)

            # Clear cache if limit exceeded
            if len(self.models) > self.max_cache_size:
                # Remove least recently used model
                oldest_lang = self.usage_order.pop(0)
                del self.models[oldest_lang]
                logger.info(f"[CACHE] Cleared spacy model for language '{oldest_lang}' (cache limit exceeded)")

            logger.info(f"[CACHE] Loaded spacy model for language '{lang_code}': {model_name}")
            return nlp

        except OSError:
            logger.error(
                f"[CACHE] Model '{model_name}' not found. Install it with: python -m spacy download {model_name}"
            )
            return None

    def cleanup(self):
        """Clear entire cache"""
        self.models.clear()
        self.usage_order.clear()
        logger.info("[CACHE] spaCy models cache cleared")
