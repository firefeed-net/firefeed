import logging
import spacy
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SpacyModelCache:
    """LRU-кэш для spaCy моделей"""

    def __init__(self, max_cache_size: int = 3):
        self.max_cache_size = max_cache_size
        self.models: Dict[str, Any] = {}
        self.usage_order: list = []  # LRU: последний использованный в конце

    def get_model(self, lang_code: str) -> Optional[Any]:
        """
        Получает spaCy модель для языка с LRU-кэшированием

        Args:
            lang_code: Код языка ('en', 'ru', 'de', 'fr')

        Returns:
            spaCy модель или None если не найдена
        """
        if lang_code in self.models:
            # Обновляем порядок использования (LRU)
            if lang_code in self.usage_order:
                self.usage_order.remove(lang_code)
            self.usage_order.append(lang_code)
            return self.models[lang_code]

        # Сопоставление языкового кода с моделью spacy
        spacy_model_map = {
            "en": "en_core_web_sm",
            "ru": "ru_core_news_sm",
            "de": "de_core_news_sm",
            "fr": "fr_core_news_sm",
        }

        model_name = spacy_model_map.get(lang_code)
        if not model_name:
            logger.warning(f"[CACHE] Языковая модель для '{lang_code}' не найдена, используем 'en_core_web_sm'")
            model_name = "en_core_web_sm"

        try:
            # Загружаем модель
            nlp = spacy.load(model_name)
            self.models[lang_code] = nlp
            self.usage_order.append(lang_code)

            # Очищаем кэш если превышен лимит
            if len(self.models) > self.max_cache_size:
                # Удаляем наименее недавно использованную модель
                oldest_lang = self.usage_order.pop(0)
                del self.models[oldest_lang]
                logger.info(f"[CACHE] Очищена spacy модель для языка '{oldest_lang}' (превышен лимит кэша)")

            logger.info(f"[CACHE] Загружена spacy модель для языка '{lang_code}': {model_name}")
            return nlp

        except OSError:
            logger.error(
                f"[CACHE] Модель '{model_name}' не найдена. Установите её командой: python -m spacy download {model_name}"
            )
            return None

    def cleanup(self):
        """Очистка всего кэша"""
        self.models.clear()
        self.usage_order.clear()
        logger.info("[CACHE] Кэш spaCy моделей очищен")
