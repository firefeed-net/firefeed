# FireFeed - AI-powered RSS aggregator and parser

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-Passing-green.svg)](https://github.com/yuremweiland/firefeed/actions)

A modern news aggregator with AI support for automatic collection, processing, and distribution of news in multiple languages.

**Official website**: https://firefeed.net

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation and Setup](#installation-and-setup)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Development](#development)
- [License](#license)

## Project Overview

FireFeed is a high-performance system for automatic collection, processing, and distribution of news content. The project uses modern machine learning technologies for intelligent text processing and provides multilingual support for international audiences.

## Key Features

### AI-powered Content Processing

- **Automatic news translation** to 4 languages (Russian, German, French, English) using modern machine learning models (Helsinki-NLP OPUS-MT, M2M100) - **optional via TRANSLATION_ENABLED**
- **Duplicate detection** using semantic analysis and vector embeddings (Sentence Transformers) - **optional via DUPLICATE_DETECTOR_ENABLED**
- **Intelligent image processing** with automatic extraction and optimization

### Multilingual Support

- Fully localized Telegram bot with support for 4 languages
- REST API with multilingual interface
- Adaptive translation system with terminology consideration

### Flexible RSS System

- **Automatic parsing** of over 50 RSS feeds from various sources
- **News categorization** by topics (world news, technology, sports, economy, etc.)
- **Personalized user subscriptions** to categories and sources
- **Custom RSS feeds** - ability to add personal sources

### Secure Architecture

- **JWT authentication** for API
- **Password encryption** using bcrypt
- **Email validation** with confirmation codes
- **Secure secret storage** through environment variables

### High Performance

- **Asynchronous architecture** based on asyncio
- **PostgreSQL connection pool** for efficient database operations
- **Task queues** for parallel translation processing
- **ML model caching** for memory optimization

## Technology Stack

### Backend
- Python 3.8+ with asyncio
- FastAPI for REST API
- PostgreSQL with pgvector for semantic search
- Redis for storing API key usage data
- aiopg for asynchronous database queries

### AI/ML
- Transformers (Hugging Face)
- Sentence Transformers for embeddings
- SpaCy for text processing
- Torch for computations

### Integrations
- Telegram Bot API
- SMTP for email notifications
- Webhook support

### Infrastructure
- Docker containerization
- systemd for service management
- nginx for proxying

## Architecture

The project consists of several key components:

1. **Telegram Bot** (`apps/telegram_bot.py`) - main user interaction interface
2. **RSS Parser Service** (`apps/rss_parser.py`) - background service for RSS feed parsing
3. **REST API** (`apps/api.py`) - web API for external integrations
4. **Translation Services** (`services/translation/`) - translation system with caching
5. **Duplicate Detector** (`services/text_analysis/duplicate_detector.py`) - ML-based duplicate detection
6. **User Management** (`services/user/user_manager.py`) - user and subscription management

### Telegram Bot

The Telegram bot serves as the primary interface for users to interact with the FireFeed system. It provides personalized news delivery, subscription management, and multilingual support.

#### Key Features

- **Personalized News Delivery**: Users receive news based on their category subscriptions in their preferred language
- **Multilingual Interface**: Full localization support for English, Russian, German, and French
- **Subscription Management**: Easy category-based subscription configuration through inline keyboards
- **Automatic Publishing**: News items are automatically published to configured Telegram channels

#### Publication Rate Limiting

To prevent spam and ensure fair usage, the bot implements sophisticated rate limiting for news publications:

##### Feed-Level Limits
Each RSS feed has configurable limits:
- `cooldown_minutes`: Minimum time between processing feed items (default: 60 minutes)
- `max_news_per_hour`: Maximum number of news items per hour from this feed (default: 10)

##### Telegram Publication Checks
Before publishing any news item to Telegram channels, the system performs two types of checks:

1. **Count-based Limiting**:
   - Counts recent publications from the same feed within the `cooldown_minutes` period
   - If count >= `max_news_per_hour`, skips publication
   - Uses data from `rss_items_telegram_bot_published` table

2. **Time-based Limiting**:
   - Checks time since last publication from the same feed
   - Minimum interval = `60 / max_news_per_hour` minutes (e.g., 6 minutes for 10 news/hour)
   - Effective limit = minimum of time-based interval and `cooldown_minutes`
   - If elapsed time < effective limit, skips publication

##### How It Works
```python
# Example: feed with cooldown_minutes=120, max_news_per_hour=1
# - Maximum 1 publication per 120 minutes
# - Minimum 60 minutes between publications (60/1 = 60)
# - Effective minimum interval: min(60, 120) = 60 minutes

# Before each publication attempt:
recent_count = get_recent_telegram_publications_count(feed_id, 120)
if recent_count >= 1:
    skip_publication()

last_time = get_last_telegram_publication_time(feed_id)
if last_time:
    elapsed = now - last_time
    min_interval = timedelta(minutes=60/1)  # 60 minutes
    cooldown_limit = timedelta(minutes=120)
    effective_limit = min(min_interval, cooldown_limit)
    if elapsed < effective_limit:
        skip_publication()
```

This ensures that even if multiple news items are processed simultaneously from the same feed, only the allowed number will be published to Telegram, preventing rate limit violations and maintaining quality user experience.

### Scalability and Reliability

- **Horizontal scaling** through microservice architecture
- **Fault tolerance** with automatic restarts and logging
- **Performance monitoring** with detailed telemetry
- **Graceful shutdown** for proper service termination

## Service Architecture

The project uses modern service-oriented architecture with dependency injection to ensure high testability and maintainability.

### RSS Services

#### RSSFetcher (`services/rss/rss_fetcher.py`)
Service for fetching and parsing RSS feeds.

**Key Features:**
- Asynchronous RSS feed fetching with semaphore support for concurrency control
- XML structure parsing with extraction of titles, content, and metadata
- Duplicate detection through built-in detector
- Media content extraction (images, videos)

**Configuration:**
```env
RSS_MAX_CONCURRENT_FEEDS=10
RSS_MAX_ENTRIES_PER_FEED=50
```

#### RSSValidator (`services/rss/rss_validator.py`)
Service for RSS feed validation.

**Key Features:**
- URL availability checking with timeouts
- Validation result caching
- RSS structure correctness determination

**Configuration:**
```env
RSS_VALIDATION_CACHE_TTL=300
RSS_REQUEST_TIMEOUT=15
```

#### RSSStorage (`services/rss/rss_storage.py`)
Service for RSS data database operations.

**Key Features:**
- Saving RSS items to database
- News translation management
- RSS feed settings retrieval (cooldowns, limits)

#### MediaExtractor (`services/rss/media_extractor.py`)
Service for extracting media content from RSS items.

**Key Features:**
- Image URL extraction from various RSS formats (media:thumbnail, enclosure)
- Video URL extraction with size checking
- Atom and RSS format support

### Translation Services

#### ModelManager (`services/translation/model_manager.py`)
ML model manager for translations.

**Key Features:**
- Lazy loading of translation models
- In-memory model caching with automatic cleanup
- GPU/CPU memory management

**Configuration:**
```env
TRANSLATION_MAX_CACHED_MODELS=15
TRANSLATION_MODEL_CLEANUP_INTERVAL=1800
TRANSLATION_DEVICE=cpu
```

#### TranslationService (`services/translation/translation_service.py`)
Main service for performing translations.

**Key Features:**
- Batch translation processing for performance optimization
- Text preprocessing and postprocessing
- Translation concurrency management

**Configuration:**
```env
TRANSLATION_MAX_CONCURRENT=3
```

#### TranslationCache (`services/translation/translation_cache.py`)
Translation result caching.

**Key Features:**
- Translation caching with TTL
- Cache size limitation
- Automatic cleanup of expired entries

**Configuration:**
```env
CACHE_DEFAULT_TTL=3600
CACHE_MAX_SIZE=10000
```

### User Services

#### TelegramUserService (`services/user/telegram_user_service.py`)
Service for managing Telegram bot users and their preferences.

**Key Features:**
- User settings management (subscriptions, language)
- Category-based subscriber retrieval
- User language preferences
- Database operations for Telegram bot users

**Interface:** `ITelegramUserService`

#### WebUserService (`services/user/web_user_service.py`)
Service for managing web users and Telegram account linking.

**Key Features:**
- Telegram link code generation and validation
- Web user to Telegram user association
- Secure linking process with expiration
- Database operations for web user management

**Interface:** `IWebUserService`

#### UserManager (`services/user/user_manager.py`)
Backward compatibility wrapper that delegates to specialized services.

**Key Features:**
- Unified interface for both Telegram and web users
- Automatic delegation to appropriate service
- Maintains existing API compatibility

**Interface:** `IUserManager`

### Dependency Injection System

#### DI Container (`di_container.py`)
Dependency injection container for service management.

**Key Features:**
- Service and factory registration
- Automatic dependency resolution
- Service lifecycle management

#### Service Configuration (`config_services.py`)
Centralized configuration of all services through environment variables.

**Configuration Example:**
```env
# RSS services
RSS_MAX_CONCURRENT_FEEDS=10
RSS_MAX_ENTRIES_PER_FEED=50
RSS_VALIDATION_CACHE_TTL=300
RSS_REQUEST_TIMEOUT=15

# Translation services
TRANSLATION_MAX_CONCURRENT=3
TRANSLATION_MAX_CACHED_MODELS=15
TRANSLATION_MODEL_CLEANUP_INTERVAL=1800
TRANSLATION_DEVICE=cpu

# Caching
CACHE_DEFAULT_TTL=3600
CACHE_MAX_SIZE=10000
CACHE_CLEANUP_INTERVAL=300

# Task queues
QUEUE_MAX_SIZE=30
QUEUE_DEFAULT_WORKERS=1
QUEUE_TASK_TIMEOUT=300
```

### Interfaces (`interfaces.py`)
Abstract interfaces for all services, providing:
- **Dependency Inversion Principle**
- **Easy testing** through mock objects
- **Implementation replacement flexibility**

### Error Handling (`exceptions.py`)
Hierarchy of custom exceptions for different error types:
- `RSSException` - RSS processing errors
- `TranslationException` - translation errors
- `DatabaseException` - database errors
- `CacheException` - caching errors

### Benefits of New Architecture

1. **High testability** - each service is tested in isolation
2. **Configuration flexibility** - all parameters configurable via environment variables
3. **Easy maintenance** - clear separation of responsibilities
4. **Scalability** - services can be easily replaced or extended
5. **Reliability** - specific error handling and graceful degradation

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+ with pgvector extension
- Telegram Bot API token

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### Basic Setup

1. Copy .env.example to .env
2. Configure real values for variables in .env file

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # for Windows: venv\Scripts\activate

# Run Telegram bot
python bot.py
```

### Running via Scripts

```bash
# Make scripts executable
chmod +x ./scripts/run_telegram_bot.sh
chmod +x ./scripts/run_rss_parser.sh
chmod +x ./scripts/run_api.sh

# Run Telegram bot
./scripts/run_telegram_bot.sh

# Run RSS parser
./scripts/run_rss_parser.sh

# Run API
./scripts/run_api.sh
```

## Configuration

### Environment Variables

Create a `.env` file in the project root directory:

```env
# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Database configuration
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=firefeed
DB_PORT=5432
DB_MINSIZE=5
DB_MAXSIZE=20

# SMTP configuration for email notifications
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=465
SMTP_EMAIL=your_email@yourdomain.com
SMTP_PASSWORD=your_smtp_password
SMTP_USE_TLS=True

# Webhook configuration for Telegram bot
WEBHOOK_LISTEN=127.0.0.1
WEBHOOK_PORT=5000
WEBHOOK_URL_PATH=webhook
WEBHOOK_URL=https://yourdomain.com/webhook

# Telegram Bot Token (get from @BotFather)
BOT_TOKEN=your_telegram_bot_token

# JWT configuration for API authentication
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis configuration for caching and task queues
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# API Key configuration
API_KEY_SALT=change_in_production
SITE_API_KEY=your_site_api_key
BOT_API_KEY=your_bot_api_key

# Optional AI features (enabled by default)
TRANSLATION_ENABLED=true          # Enable/disable automatic news translation
DUPLICATE_DETECTOR_ENABLED=true   # Enable/disable ML-based duplicate detection

# AI Model configuration
TRANSLATION_MODEL=facebook/m2m100_418M                    # Translation model (M2M100, Helsinki-NLP, etc.)
EMBEDDING_SENTENCE_TRANSFORMER_MODEL=paraphrase-multilingual-MiniLM-L12-v2  # Sentence transformer for embeddings
SPACY_EN_MODEL=en_core_web_sm                              # English spaCy model
SPACY_RU_MODEL=ru_core_news_sm                             # Russian spaCy model
SPACY_DE_MODEL=de_core_news_sm                             # German spaCy model
SPACY_FR_MODEL=fr_core_news_sm                             # French spaCy model
```

### Optional AI Features Configuration

FireFeed provides optional AI-powered features that can be enabled or disabled based on your needs:

#### TRANSLATION_ENABLED
- **Default**: `true`
- **Description**: Controls automatic translation of news articles to multiple languages
- **Impact**: When disabled, news items will only be available in their original language
- **Use case**: Disable to reduce computational load or when translations are not needed

#### DUPLICATE_DETECTOR_ENABLED
- **Default**: `true`
- **Description**: Controls ML-based duplicate detection using semantic analysis
- **Impact**: When disabled, all news items will be processed without duplicate checking
- **Use case**: Disable for faster processing or when duplicate detection is handled externally

### AI Model Configuration

FireFeed allows customization of the AI models used for translation, embeddings, and text processing:

#### TRANSLATION_MODEL
- **Default**: `facebook/m2m100_418M`
- **Description**: Specifies the translation model from Hugging Face Transformers
- **Supported models**: M2M100, Helsinki-NLP OPUS-MT, MarianMT, MBart, etc.
- **Example**: `Helsinki-NLP/opus-mt-en-ru` for Helsinki-NLP models

#### EMBEDDING_SENTENCE_TRANSFORMER_MODEL
- **Default**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Description**: Sentence transformer model for generating text embeddings
- **Supported models**: Any SentenceTransformer-compatible model from Hugging Face
- **Example**: `all-MiniLM-L6-v2` for faster, smaller model

#### SPACY_*_MODEL
- **Default**: `en_core_web_sm`, `ru_core_news_sm`, `de_core_news_sm`, `fr_core_news_sm`
- **Description**: spaCy language models for text processing and linguistic analysis
- **Supported models**: Any spaCy model compatible with the language
- **Example**: `en_core_web_trf` for transformer-based English model

### Systemd Services

For production environments, systemd services are recommended.

**Telegram Bot Service** (`/etc/systemd/system/firefeed-bot.service`):

```ini
[Unit]
Description=FireFeed Telegram Bot Service
After=network.target

[Service]
Type=simple
User=firefeed
Group=firefeed
WorkingDirectory=/path/to/firefeed/

ExecStart=/path/to/firefeed/scripts/run_telegram_bot.sh

Restart=on-failure
RestartSec=10

TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGTERM
SendSIGKILL=yes

[Install]
WantedBy=multi-user.target
```

**API Service** (`/etc/systemd/system/firefeed-api.service`):

```ini
[Unit]
Description=Firefeed News API (FastAPI)
After=network.target
After=postgresql@17-main.service
Wants=postgresql@17-main.service

[Service]
Type=simple
User=firefeed
Group=firefeed

WorkingDirectory=/path/to/firefeed/
ExecStart=/path/to/firefeed/scripts/run_api.sh

Restart=always
RestartSec=5

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

Example configuration for webhook and FastAPI operation:

```nginx
upstream fastapi_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your_domain.com;

    location /webhook {
        proxy_pass http://127.0.0.1:5000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://fastapi_app;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## API Documentation

After starting the API server, documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Main endpoints:

- `GET /api/v1/news` - get news list
- `POST /api/v1/users/register` - user registration
- `GET /api/v1/subscriptions` - subscription management

## Development

### Development Setup

```bash
# Clone repository from GitHub
git clone https://github.com/yuremweiland/firefeed.git
# or GitVerse
git clone https://gitverse.ru/yuryweiland/firefeed.git
cd firefeed

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

All tests

```bash
pytest tests/
```

Specific module

```bash
pytest tests/test_models.py
```

Stop on first failure

```bash
pytest tests/ -x
```

Short output

```bash
pytest tests/ --tb=short
```

### Project Structure

```
firefeed/
├── apps/                       # Application entry points
│   ├── __init__.py
│   ├── rss_parser/             # RSS parser application
│   │   └── __main__.py         # RSS parser entry point
│   ├── telegram_bot/           # Telegram bot application
│   │   ├── __init__.py
│   │   ├── __main__.py         # Telegram bot entry point
│   │   ├── bot.py              # Main bot logic
│   │   ├── config.py           # Bot configuration
│   │   ├── translations.py     # Bot translations
│   │   ├── handlers/           # Telegram bot handlers
│   │   │   ├── __init__.py
│   │   │   ├── callback_handlers.py # Callback query handlers
│   │   │   ├── command_handlers.py # Command handlers
│   │   │   ├── error_handlers.py   # Error handlers
│   │   │   └── message_handlers.py # Message handlers
│   │   ├── models/             # Telegram bot models
│   │   │   ├── __init__.py
│   │   │   ├── rss_item.py     # RSS item models
│   │   │   ├── telegram_models.py # Telegram models
│   │   │   └── user_state.py   # User state models
│   │   ├── services/           # Telegram bot services
│   │   │   ├── __init__.py
│   │   │   ├── api_service.py      # API communication service
│   │   │   ├── database_service.py # Database service
│   │   │   ├── rss_service.py      # RSS service
│   │   │   ├── telegram_service.py # Telegram messaging service
│   │   │   └── user_state_service.py # User state service
│   │   └── utils/              # Telegram bot utilities
│   │       ├── __init__.py
│   │       ├── cleanup_utils.py    # Cleanup utilities
│   │       ├── formatting_utils.py # Message formatting
│   │       ├── keyboard_utils.py   # Keyboard utilities
│   │       └── validation_utils.py # Validation utilities
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
└── README.md                   # This file
```

## License

This project is distributed under the MIT license. See LICENSE file for details.