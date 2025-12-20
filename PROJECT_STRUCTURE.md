# Project Structure

```
firefeed/
├── apps/                       # Application entry points
│   ├── __init__.py
│   ├── rss_parser/             # RSS parser application
│   │   └── __main__.py         # RSS parser entry point
│   └── api/                    # FastAPI REST API application
│       ├── __init__.py
│       ├── __main__.py         # FastAPI entry point
│       ├── app.py              # FastAPI application
│       ├── database.py         # Database connection
│       ├── deps.py             # Dependencies
│       ├── middleware.py       # Custom middleware
│       ├── models.py           # Pydantic models
│       ├── websocket.py        # WebSocket support
│       ├── email_service/      # Email service
│       │   ├── __init__.py
│       │   ├── sender.py       # Email sending
│       │   └── templates/      # Email templates
│       │       ├── password_reset_email_de.html
│       │       ├── password_reset_email_en.html
│       │       ├── password_reset_email_ru.html
│       │       ├── registration_success_email_de.html
│       │       ├── registration_success_email_en.html
│       │       ├── registration_success_email_ru.html
│       │       ├── verification_email_de.html
│       │       ├── verification_email_en.html
│       │       └── verification_email_ru.html
│       └── routers/            # API endpoints
│           ├── __init__.py
│           ├── api_keys.py     # API key management
│           ├── auth.py         # Authentication
│           ├── categories.py   # News categories
│           ├── rss_feeds.py    # RSS feed management
│           ├── rss_items.py    # RSS items
│           ├── rss.py          # RSS operations
│           ├── telegram.py     # Telegram integration
│           └── users.py        # User management
├── config/                     # Configuration modules
│   ├── logging_config.py       # Logging configuration
│   └── services_config.py      # Service configuration
├── database/                   # Database related files
│   └── migrations.sql          # Database migrations
├── exceptions/                 # Custom exceptions
│   ├── __init__.py
│   ├── base_exceptions.py      # Base exception classes
│   ├── cache_exceptions.py     # Cache related exceptions
│   ├── database_exceptions.py  # Database exceptions
│   ├── rss_exceptions.py       # RSS processing exceptions
│   ├── service_exceptions.py   # Service exceptions
│   └── translation_exceptions.py # Translation exceptions
├── interfaces/                 # Service interfaces
│   ├── __init__.py
│   ├── core_interfaces.py      # Core interfaces
│   ├── repository_interfaces.py # Repository interfaces
│   ├── rss_interfaces.py       # RSS interfaces
│   ├── translation_interfaces.py # Translation interfaces
│   └── user_interfaces.py      # User interfaces
├── repositories/               # Data access layer
│   ├── __init__.py
│   ├── api_key_repository.py   # API key repository
│   ├── category_repository.py  # Category repository
│   ├── rss_feed_repository.py  # RSS feed repository
│   ├── rss_item_repository.py  # RSS item repository
│   ├── source_repository.py    # Source repository
│   ├── telegram_repository.py  # Telegram repository
│   └── user_repository.py      # User repository
├── services/                   # Service-oriented architecture
│   ├── database_pool_adapter.py # Database connection pool
│   ├── maintenance_service.py  # System maintenance
│   ├── rss/                    # RSS processing services
│   │   ├── __init__.py
│   │   ├── media_extractor.py  # Media content extraction
│   │   ├── rss_fetcher.py      # RSS feed fetching
│   │   ├── rss_manager.py      # RSS processing orchestration
│   │   ├── rss_parser.py       # RSS parsing logic
│   │   ├── rss_storage.py      # RSS data storage
│   │   └── rss_validator.py    # RSS feed validation
│   ├── text_analysis/          # Text analysis and ML services
│   │   ├── __init__.py
│   │   ├── duplicate_detector.py # ML-based duplicate detection
│   │   └── embeddings_processor.py # Text embeddings and processing
│   ├── translation/            # Translation services
│   │   ├── __init__.py
│   │   ├── model_manager.py    # ML model management
│   │   ├── task_queue.py       # Translation task queue
│   │   ├── terminology_dict.py # Translation terminology
│   │   ├── translation_cache.py # Translation caching
│   │   ├── translation_service.py # Translation processing
│   │   └── translations.py     # Translation messages
│   └── user/                   # User management services
│       ├── __init__.py
│       ├── telegram_user_service.py # Telegram bot user management
│       ├── web_user_service.py # Web user management and Telegram linking
│       └── user_manager.py     # Backward compatibility wrapper
├── tests/                      # Unit and integration tests
│   ├── __init__.py
│   ├── test_api_keys.py        # API key tests
│   ├── test_bot.py             # Telegram bot tests
│   ├── test_database.py        # Database tests
│   ├── test_di_integration.py  # Dependency injection tests
│   ├── test_email.py           # Email service tests
│   ├── test_models.py          # Model tests
│   ├── test_registration_success_email.py # Email template tests
│   ├── test_rss_manager.py     # RSS manager tests
│   ├── test_services.py        # Service tests
│   ├── test_user_services.py   # User services tests
│   ├── test_user_state_service.py # User state service tests
│   └── test_utils.py           # Utility tests
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── api.py                  # API utilities
│   ├── cache.py                # Caching utilities
│   ├── cleanup.py              # Cleanup utilities
│   ├── database.py             # Database utilities
│   ├── image.py                # Image processing
│   ├── media_extractors.py     # Media extraction
│   ├── retry.py                # Retry mechanisms
│   ├── text.py                 # Text processing
│   └── video.py                # Video processing
├── scripts/                    # Startup scripts
│   ├── run_api.sh              # API startup script
│   ├── run_rss_parser.sh       # RSS parser startup script
│   └── run_telegram_bot.sh     # Telegram bot startup script
├── di_container.py             # Dependency injection container
├── requirements.txt            # Python dependencies
├── .dockerignore               # Docker ignore file
├── .env.example                # Environment variables example
├── .gitignore                  # Git ignore file
├── CODE_OF_CONDUCT.md          # Code of conduct
├── CONTRIBUTING.md             # Contribution guidelines
├── docker-compose.yml          # Docker compose configuration
├── Dockerfile                  # Docker image definition
├── LICENSE                     # License file
├── PROJECT_STRUCTURE.md        # This file
└── README.md                   # README file