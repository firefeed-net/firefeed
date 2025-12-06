# config_services.py - Service configuration via environment variables
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class RSSConfig:
    """Configuration for RSS services"""
    max_concurrent_feeds: int = 10
    max_entries_per_feed: int = 50
    validation_cache_ttl: int = 300  # 5 minutes
    request_timeout: int = 15
    max_total_rss_items: int = 1000

    @classmethod
    def from_env(cls) -> 'RSSConfig':
        return cls(
            max_concurrent_feeds=int(os.getenv('RSS_MAX_CONCURRENT_FEEDS', '10')),
            max_entries_per_feed=int(os.getenv('RSS_MAX_ENTRIES_PER_FEED', '50')),
            validation_cache_ttl=int(os.getenv('RSS_VALIDATION_CACHE_TTL', '300')),
            request_timeout=int(os.getenv('RSS_REQUEST_TIMEOUT', '15')),
            max_total_rss_items=int(os.getenv('RSS_MAX_TOTAL_ITEMS', '1000'))
        )


@dataclass
class TranslationModelsConfig:
    """Configuration for translation models"""
    translation_model: str = "facebook/m2m100_418M"

    @classmethod
    def from_env(cls) -> 'TranslationModelsConfig':
        return cls(
            translation_model=os.getenv('TRANSLATION_MODEL', 'facebook/m2m100_418M')
        )


@dataclass
class EmbeddingModelsConfig:
    """Configuration for embedding models"""
    sentence_transformer_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    @classmethod
    def from_env(cls) -> 'EmbeddingModelsConfig':
        return cls(
            sentence_transformer_model=os.getenv('EMBEDDING_SENTENCE_TRANSFORMER_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
        )


@dataclass
class SpacyModelsConfig:
    """Configuration for spaCy models"""
    en_model: str = "en_core_web_sm"
    ru_model: str = "ru_core_news_sm"
    de_model: str = "de_core_news_sm"
    fr_model: str = "fr_core_news_sm"

    @classmethod
    def from_env(cls) -> 'SpacyModelsConfig':
        return cls(
            en_model=os.getenv('SPACY_EN_MODEL', 'en_core_web_sm'),
            ru_model=os.getenv('SPACY_RU_MODEL', 'ru_core_news_sm'),
            de_model=os.getenv('SPACY_DE_MODEL', 'de_core_news_sm'),
            fr_model=os.getenv('SPACY_FR_MODEL', 'fr_core_news_sm')
        )


@dataclass
class TranslationConfig:
    """Configuration for translation services"""
    models: TranslationModelsConfig
    max_concurrent_translations: int = 3
    max_cached_models: int = 15
    model_cleanup_interval: int = 1800  # 30 minutes
    default_device: str = "cpu"
    max_workers: int = 4
    translation_enabled: bool = True

    @classmethod
    def from_env(cls) -> 'TranslationConfig':
        return cls(
            models=TranslationModelsConfig.from_env(),
            max_concurrent_translations=int(os.getenv('TRANSLATION_MAX_CONCURRENT', '3')),
            max_cached_models=int(os.getenv('TRANSLATION_MAX_CACHED_MODELS', '15')),
            model_cleanup_interval=int(os.getenv('TRANSLATION_CLEANUP_INTERVAL', '1800')),
            default_device=os.getenv('TRANSLATION_DEVICE', 'cpu'),
            max_workers=int(os.getenv('TRANSLATION_MAX_WORKERS', '4')),
            translation_enabled=os.getenv('TRANSLATION_ENABLED', 'true').lower() == 'true'
        )


@dataclass
class CacheConfig:
    """Configuration for caching services"""
    default_ttl: int = 3600  # 1 hour
    max_cache_size: int = 10000
    cleanup_interval: int = 300  # 5 minutes

    @classmethod
    def from_env(cls) -> 'CacheConfig':
        return cls(
            default_ttl=int(os.getenv('CACHE_DEFAULT_TTL', '3600')),
            max_cache_size=int(os.getenv('CACHE_MAX_SIZE', '10000')),
            cleanup_interval=int(os.getenv('CACHE_CLEANUP_INTERVAL', '300'))
        )


@dataclass
class QueueConfig:
    """Configuration for queue services"""
    max_queue_size: int = 30
    default_workers: int = 1
    task_timeout: int = 300  # 5 minutes

    @classmethod
    def from_env(cls) -> 'QueueConfig':
        return cls(
            max_queue_size=int(os.getenv('QUEUE_MAX_SIZE', '30')),
            default_workers=int(os.getenv('QUEUE_DEFAULT_WORKERS', '1')),
            task_timeout=int(os.getenv('QUEUE_TASK_TIMEOUT', '300'))
        )


@dataclass
class DeduplicationConfig:
    """Configuration for deduplication services"""
    embedding_models: EmbeddingModelsConfig
    spacy_models: SpacyModelsConfig
    duplicate_detector_enabled: bool = True

    @classmethod
    def from_env(cls) -> 'DeduplicationConfig':
        return cls(
            embedding_models=EmbeddingModelsConfig.from_env(),
            spacy_models=SpacyModelsConfig.from_env(),
            duplicate_detector_enabled=os.getenv('DUPLICATE_DETECTOR_ENABLED', 'true').lower() == 'true'
        )


@dataclass
class TelegramBotConfig:
    """Configuration for Telegram bot job queue"""
    rss_monitor_interval: int = 180  # 3 minutes
    rss_monitor_first_delay: int = 10  # 10 seconds
    rss_monitor_misfire_grace_time: int = 600  # 10 minutes
    user_cleanup_interval: int = 3600  # 1 hour
    user_cleanup_first_delay: int = 60  # 1 minute
    send_locks_cleanup_interval: int = 3600  # 1 hour
    send_locks_cleanup_first_delay: int = 120  # 2 minutes

    @classmethod
    def from_env(cls) -> 'TelegramBotConfig':
        return cls(
            rss_monitor_interval=int(os.getenv('BOT_RSS_MONITOR_INTERVAL', '180')),
            rss_monitor_first_delay=int(os.getenv('BOT_RSS_MONITOR_FIRST_DELAY', '10')),
            rss_monitor_misfire_grace_time=int(os.getenv('BOT_RSS_MONITOR_MISFIRE_GRACE_TIME', '600')),
            user_cleanup_interval=int(os.getenv('BOT_USER_CLEANUP_INTERVAL', '3600')),
            user_cleanup_first_delay=int(os.getenv('BOT_USER_CLEANUP_FIRST_DELAY', '60')),
            send_locks_cleanup_interval=int(os.getenv('BOT_SEND_LOCKS_CLEANUP_INTERVAL', '3600')),
            send_locks_cleanup_first_delay=int(os.getenv('BOT_SEND_LOCKS_CLEANUP_FIRST_DELAY', '120'))
        )


@dataclass
class ServiceConfig:
    """Main service configuration"""
    rss: RSSConfig
    translation: TranslationConfig
    cache: CacheConfig
    queue: QueueConfig
    deduplication: DeduplicationConfig
    telegram_bot: TelegramBotConfig

    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        return cls(
            rss=RSSConfig.from_env(),
            translation=TranslationConfig.from_env(),
            cache=CacheConfig.from_env(),
            queue=QueueConfig.from_env(),
            deduplication=DeduplicationConfig.from_env(),
            telegram_bot=TelegramBotConfig.from_env()
        )


# Global configuration instance
_config: Optional[ServiceConfig] = None


def get_service_config() -> ServiceConfig:
    """Get global service configuration"""
    global _config
    if _config is None:
        _config = ServiceConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset configuration (for testing)"""
    global _config
    _config = None