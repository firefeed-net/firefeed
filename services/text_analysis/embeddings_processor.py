import re
import spacy
import asyncio
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Optional, Dict, Any
import logging
from utils.text import TextProcessor
from config.services_config import get_service_config

logger = logging.getLogger(__name__)


class FireFeedEmbeddingsProcessor:
    # Global cache for singleton
    _instance = None
    _model_cache = {}
    _spacy_cache = {}
    _spacy_usage_order = []

    def __new__(cls, model_name: Optional[str] = None, device: str = "cpu", max_spacy_cache: int = 3):
        """Singleton pattern for model caching"""
        if model_name is None:
            config = get_service_config()
            model_name = config.deduplication.embedding_models.sentence_transformer_model
        cache_key = f"{model_name}_{device}_{max_spacy_cache}"
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self, model_name: Optional[str] = None, device: str = "cpu", max_spacy_cache: int = 3
    ):
        if model_name is None:
            config = get_service_config()
            model_name = config.deduplication.embedding_models.sentence_transformer_model
        """
        Initialize embeddings processor with model caching

        Args:
            model_name: Name of sentence-transformers model
            device: Device for model (cpu/cuda)
            max_spacy_cache: Maximum number of cached spacy models
        """
        if self._initialized:
            return

        self.model_name = model_name
        self.device = device
        self.max_spacy_cache = max_spacy_cache

        # Load or get SentenceTransformer model from cache
        model_key = f"{model_name}_{device}"
        if model_key not in self._model_cache:
            logger.info(f"[EMBEDDINGS] Loading SentenceTransformer model: {model_name}")
            self._model_cache[model_key] = SentenceTransformer(model_name, device=device)
        else:
            logger.info(f"[EMBEDDINGS] Using cached SentenceTransformer model: {model_name}")
        self.model = self._model_cache[model_key]

        self.embedding_dim = self._get_embedding_dimension()

        self._initialized = True

    def _get_embedding_dimension(self) -> int:
        """Get embedding dimension of the model"""
        sample_text = "test"
        embedding = self.model.encode(sample_text)
        return len(embedding)

    def _get_spacy_model(self, lang_code: str) -> Optional[spacy.Language]:
        """Gets spacy model for language with global LRU caching"""
        if lang_code in self._spacy_cache:
            # Update usage order (LRU)
            if lang_code in self._spacy_usage_order:
                self._spacy_usage_order.remove(lang_code)
            self._spacy_usage_order.append(lang_code)
            logger.info(f"[EMBEDDINGS] Using cached spacy model for language '{lang_code}'")
            return self._spacy_cache[lang_code]

        config = get_service_config()
        spacy_model_map = {
            "en": config.deduplication.spacy_models.en_model,
            "ru": config.deduplication.spacy_models.ru_model,
            "de": config.deduplication.spacy_models.de_model,
            "fr": config.deduplication.spacy_models.fr_model,
        }

        model_name = spacy_model_map.get(lang_code)
        if not model_name:
            logger.warning(f"[EMBEDDINGS] Language model for '{lang_code}' not found, using 'en_core_web_sm'")
            model_name = "en_core_web_sm"

        try:
            nlp = spacy.load(model_name)
            self._spacy_cache[lang_code] = nlp
            self._spacy_usage_order.append(lang_code)

            # Clear cache if limit exceeded
            if len(self._spacy_cache) > self.max_spacy_cache:
                # Remove least recently used model
                oldest_lang = self._spacy_usage_order.pop(0)
                del self._spacy_cache[oldest_lang]
                logger.info(f"[EMBEDDINGS] Cleared spacy model for language '{oldest_lang}' (cache limit exceeded)")

            logger.info(f"[EMBEDDINGS] Loaded spacy model for language '{lang_code}': {model_name}")
            return nlp
        except OSError:
            logger.error(
                f"[EMBEDDINGS] Model '{model_name}' not found. Install it with: python -m spacy download {model_name}"
            )
            return None

    async def normalize_text(self, text: str, lang_code: str = "en") -> str:
        """
        Normalize text: remove HTML, stop-words, lemmatization

        Args:
            text: Original text
            lang_code: Language code

        Returns:
            Normalized text
        """
        loop = asyncio.get_event_loop()

        # HTML removal
        text = await loop.run_in_executor(None, TextProcessor.clean, text)

        # Getting spacy model
        nlp = self._get_spacy_model(lang_code)
        if nlp is None:
            # If model not loaded, apply simple cleaning
            text = await loop.run_in_executor(None, lambda t: re.sub(r"\s+", " ", t).strip(), text)
            return text

        # Processing through spacy
        doc = await loop.run_in_executor(None, nlp, text)

        # Lemmatization and stop-word removal
        tokens = []
        for token in doc:
            if not token.is_stop and not token.is_punct and not token.is_space:
                tokens.append(token.lemma_.lower())

        normalized = " ".join(tokens)
        return normalized

    @classmethod
    def clear_cache(cls):
        """Clear global model cache (for testing or forced reload)"""
        cls._instance = None
        cls._model_cache.clear()
        cls._spacy_cache.clear()
        cls._spacy_usage_order.clear()
        logger.info("[EMBEDDINGS] Global model cache cleared")

    async def generate_embedding(self, text: str, lang_code: str = "en") -> List[float]:
        """
        Generate embedding for text

        Args:
            text: Text for embedding
            lang_code: Language code

        Returns:
            Embedding as list of float
        """
        loop = asyncio.get_event_loop()
        normalized_text = await self.normalize_text(text, lang_code)
        embedding = await loop.run_in_executor(None, lambda: self.model.encode(normalized_text, show_progress_bar=False))
        return embedding.tolist()

    async def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity (0-1)
        """
        loop = asyncio.get_event_loop()
        similarity = await loop.run_in_executor(None, self._calculate_similarity_sync, embedding1, embedding2)
        return similarity

    def _calculate_similarity_sync(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Synchronous version of similarity calculation for executor execution"""
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        return float(similarity)

    def get_dynamic_threshold(self, text_length: int, text_type: str = "content") -> float:
        """
        Dynamic similarity threshold based on text length and type

        Args:
            text_length: Text length (characters)
            text_type: Text type ('title' or 'content')

        Returns:
            Similarity threshold
        """
        base_threshold = 0.9

        # Adjustment by type
        if text_type == "title":
            base_threshold = 0.85  # Softer for titles
        elif text_type == "content":
            base_threshold = 0.95  # Stricter for articles

        # Adjustment by length
        if text_length < 50:  # Short texts
            base_threshold -= 0.05
        elif text_length > 1000:  # Long texts
            base_threshold += 0.02

        # Constraints
        return max(0.7, min(0.98, base_threshold))

    async def combine_texts(self, title: str, content: str, lang_code: str = "en") -> str:
        """
        Combine title and content for embedding

        Args:
            title: Title
            content: Content
            lang_code: Language code

        Returns:
            Combined text
        """
        normalized_title, normalized_content = await asyncio.gather(
            self.normalize_text(title, lang_code),
            self.normalize_text(content, lang_code)
        )

        # Limit content length
        content_preview = normalized_content[:500] if len(normalized_content) > 500 else normalized_content

        return f"{normalized_title} {content_preview}"