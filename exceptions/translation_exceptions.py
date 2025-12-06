# exceptions/translation_exceptions.py - Translation-related exceptions
from typing import Optional, Dict, Any
from .base_exceptions import FireFeedException


class TranslationException(FireFeedException):
    """Base exception for translation operations"""
    pass


class TranslationModelError(TranslationException):
    """Exception raised when translation model fails"""

    def __init__(self, model_name: str, error: str, details: Optional[Dict[str, Any]] = None):
        message = f"Translation model '{model_name}' error: {error}"
        super().__init__(message, details)
        self.model_name = model_name
        self.error = error


class TranslationServiceError(TranslationException):
    """Exception raised when translation service fails"""

    def __init__(self, source_lang: str, target_lang: str, error: str, details: Optional[Dict[str, Any]] = None):
        message = f"Translation service error for {source_lang} -> {target_lang}: {error}"
        super().__init__(message, details)
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.error = error