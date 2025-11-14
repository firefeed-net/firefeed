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

- **Automatic news translation** to 4 languages (Russian, German, French, English) using modern machine learning models (Helsinki-NLP OPUS-MT, M2M100)
- **Duplicate detection** using semantic analysis and vector embeddings (Sentence Transformers)
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

1. **Telegram Bot** (`bot.py`) - main user interaction interface
2. **RSS Parser Service** (`rss_parser.py`) - background service for RSS feed parsing
3. **REST API** (`api/main.py`) - web API for external integrations
4. **Translation Engine** (`firefeed_translator.py`) - translation system with caching
5. **Duplicate Detector** (`firefeed_dublicate_detector.py`) - ML-based duplicate detection
6. **User Management** (`user_manager.py`) - user and subscription management

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
chmod +x ./run_bot.sh
chmod +x ./run_api.sh

# Run bot
./run_bot.sh

# Run API
./run_api.sh
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
# Alternative name used in some places
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token

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
```

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
WorkingDirectory=/var/www/firefeed/data/integrations/telegram

ExecStart=/var/www/firefeed/data/integrations/telegram/run_bot.sh

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

WorkingDirectory=/var/www/firefeed/data/integrations/telegram
ExecStart=/var/www/firefeed/data/integrations/telegram/run_api.sh

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
├── services/                    # Service-oriented architecture
│   ├── rss/                    # RSS services
│   │   ├── __init__.py
│   │   ├── rss_fetcher.py     # RSS parser
│   │   ├── rss_validator.py   # Validator
│   │   ├── rss_storage.py     # Storage
│   │   ├── media_extractor.py # Media extraction
│   │   └── rss_manager.py     # Composite manager
│   └── translation/           # Translation services
│       ├── __init__.py
│       ├── model_manager.py   # ML model manager
│       ├── translation_service.py # Translation service
│       └── translation_cache.py   # Caching
├── interfaces.py              # Abstract interfaces
├── di_container.py            # Dependency injection
├── config_services.py         # Environment-based configuration
├── exceptions.py              # Custom exceptions
├── rss_manager.py             # Compatibility adapter
└── tests/test_services.py     # New service tests
```

## License

This project is distributed under the MIT license. See LICENSE file for details.