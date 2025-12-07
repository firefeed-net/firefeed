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
class DatabaseConfig:
    """Configuration for database connection"""
    host: str = "localhost"
    user: str = "your_db_user"
    password: str = "your_db_password"
    name: str = "firefeed"
    port: int = 5432
    minsize: int = 5
    maxsize: int = 20

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'your_db_user'),
            password=os.getenv('DB_PASSWORD', 'your_db_password'),
            name=os.getenv('DB_NAME', 'firefeed'),
            port=int(os.getenv('DB_PORT', '5432')),
            minsize=int(os.getenv('DB_MINSIZE', '5')),
            maxsize=int(os.getenv('DB_MAXSIZE', '20'))
        )


@dataclass
class RedisConfig:
    """Configuration for Redis connection"""
    host: str = "localhost"
    port: int = 6379
    username: Optional[str] = None
    password: Optional[str] = None
    db: int = 0

    @classmethod
    def from_env(cls) -> 'RedisConfig':
        return cls(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            username=os.getenv('REDIS_USERNAME') or None,
            password=os.getenv('REDIS_PASSWORD') or None,
            db=int(os.getenv('REDIS_DB', '0'))
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
    database: DatabaseConfig
    redis: RedisConfig
    rss: RSSConfig
    translation: TranslationConfig
    cache: CacheConfig
    queue: QueueConfig
    deduplication: DeduplicationConfig
    telegram_bot: TelegramBotConfig
    # Additional config keys
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    http_images_root_dir: str = ""
    images_root_dir: str = ""
    videos_root_dir: str = ""
    http_videos_root_dir: str = ""
    redis_config: Dict[str, Any] = None
    site_api_key: Optional[str] = None
    bot_api_key: Optional[str] = None
    bot_token: Optional[str] = None
    api_base_url: str = "http://127.0.0.1:8000/api/v1"
    webhook_listen: str = "127.0.0.1"
    webhook_port: int = 5000
    webhook_url_path: str = "webhook"
    webhook_url: str = ""
    webhook_config: Dict[str, Any] = None
    channel_id_ru: str = "-1002584789230"
    channel_id_de: str = "-1002959373215"
    channel_id_fr: str = "-1002910849909"
    channel_id_en: str = "-1003035894895"
    channel_categories: str = "world,technology,lifestyle,politics,economy,autos,sports"
    user_data_ttl_seconds: int = 86400
    rss_parser_media_type_priority: str = "image"
    default_user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 FireFeed/1.0"

    def __post_init__(self):
        if self.redis_config is None:
            self.redis_config = {
                'host': self.redis.host,
                'port': self.redis.port,
                'username': self.redis.username,
                'password': self.redis.password,
                'db': self.redis.db
            }
        if self.webhook_config is None:
            self.webhook_config = {
                'listen': self.webhook_listen,
                'port': self.webhook_port,
                'webhook_url': self.webhook_url,
                'url_path': self.webhook_url_path
            }

    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        return cls(
            database=DatabaseConfig.from_env(),
            redis=RedisConfig.from_env(),
            rss=RSSConfig.from_env(),
            translation=TranslationConfig.from_env(),
            cache=CacheConfig.from_env(),
            queue=QueueConfig.from_env(),
            deduplication=DeduplicationConfig.from_env(),
            telegram_bot=TelegramBotConfig.from_env(),
            jwt_secret_key=os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            jwt_algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
            jwt_access_token_expire_minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
            http_images_root_dir=os.getenv('HTTP_IMAGES_ROOT_DIR', ''),
            images_root_dir=os.getenv('IMAGES_ROOT_DIR', ''),
            videos_root_dir=os.getenv('VIDEOS_ROOT_DIR', ''),
            http_videos_root_dir=os.getenv('HTTP_VIDEOS_ROOT_DIR', ''),
            site_api_key=os.getenv('SITE_API_KEY'),
            bot_api_key=os.getenv('BOT_API_KEY'),
            bot_token=os.getenv('BOT_TOKEN'),
            api_base_url=os.getenv('API_BASE_URL', 'http://127.0.0.1:8000/api/v1'),
            webhook_listen=os.getenv('WEBHOOK_LISTEN', '127.0.0.1'),
            webhook_port=int(os.getenv('WEBHOOK_PORT', '5000')),
            webhook_url_path=os.getenv('WEBHOOK_URL_PATH', 'webhook'),
            webhook_url=os.getenv('WEBHOOK_URL', ''),
            channel_id_ru=os.getenv('CHANNEL_ID_RU', '-1002584789230'),
            channel_id_de=os.getenv('CHANNEL_ID_DE', '-1002959373215'),
            channel_id_fr=os.getenv('CHANNEL_ID_FR', '-1002910849909'),
            channel_id_en=os.getenv('CHANNEL_ID_EN', '-1003035894895'),
            channel_categories=os.getenv('CHANNEL_CATEGORIES', 'world,technology,lifestyle,politics,economy,autos,sports'),
            user_data_ttl_seconds=int(os.getenv('USER_DATA_TTL_SECONDS', '86400')),
            rss_parser_media_type_priority=os.getenv('RSS_PARSER_MEDIA_TYPE_PRIORITY', 'image'),
            default_user_agent=os.getenv('DEFAULT_USER_AGENT', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 FireFeed/1.0')
        )

    def get(self, key: str, default=None):
        """Dict-like get method for compatibility"""
        attr_name = key.lower().replace('_', '_')
        return getattr(self, attr_name, default)


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