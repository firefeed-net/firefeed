# FireFeed - AI-powered RSS-parser and aggregator

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-Passing-green.svg)](https://github.com/firefeed-net/firefeed/actions)

A modern RSS-parser with AI support for automatic collection, processing, and distribution of news in multiple languages.

**Official website**: https://firefeed.net

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Microservices](#microservices)
- [Installation and Setup](#installation-and-setup)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Project Structure](#project-structure)
- [License](LICENSE)

## Project Overview

FireFeed is a high-performance parsing system for automatic collection, processing, and distribution of news content. The project uses modern machine learning technologies for intelligent text processing and provides multilingual support for international audiences.

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
- Python 3.11+ with asyncio
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

FireFeed uses a **microservices architecture** with three independent services that communicate via HTTP APIs:

```
┌─────────────────────────────────────────────────────────────────┐
│                        FireFeed Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  Telegram Bot   │  │   RSS Parser     │  │   REST API      │ │
│  │                 │  │                  │  │                 │ │
│  │ • User Interface│  │ • Feed Parsing   │  │ • Public API    │ │
│  │ • Notifications │  │ • Media Extract  │  │ • Internal API  │ │
│  │ • Subscriptions │  │ • Duplicate Det  │  │ • Auth & Users  │ │
│  │ • Multilingual  │  │ • API Integration│  │ • Categories    │ │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬────────┘ │
│           │                    │                     │          │
│           └────────────────────┼─────────────────────┘          │
│                                │                                │
│                    ┌───────────▼────────────┐                   │
│                    │   Shared Services      │                   │
│                    │                        │                   │
│                    │ • PostgreSQL Database  │                   │
│                    │ • Redis Cache          │                   │
│                    │ • ML Models            │                   │
│                    │ • Translation          │                   │
│                    └────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Scalability and Reliability

- **Horizontal scaling** through microservice architecture
- **Fault tolerance** with automatic restarts and logging
- **Performance monitoring** with detailed telemetry
- **Graceful shutdown** for proper service termination

## Microservices

### 1. FireFeed API ([firefeed-api](https://github.com/firefeed-net/firefeed-api.git))

REST API service for external integrations and internal microservice communication.

**Key Features:**
- Public REST API for external consumers
- Internal API for microservice communication
- JWT authentication and user management
- RSS feed and item management
- Category and source organization
- Translation and media services
- Health checks and Prometheus metrics

**Tech Stack:** FastAPI, PostgreSQL, Redis, SQLAlchemy

**Documentation:** [firefeed-api/README.md](https://github.com/firefeed-net/firefeed-api/blob/main/README.md)

### 2. FireFeed RSS Parser ([firefeed-rss-parser](https://github.com/firefeed-net/firefeed-rss-parser.git))

Background service for RSS feed parsing and processing.

**Key Features:**
- Asynchronous RSS/Atom feed parsing
- Media content extraction (images, videos)
- Duplicate detection using semantic analysis
- Integration with FireFeed API
- Concurrent feed processing
- Health monitoring and metrics

**Tech Stack:** Python asyncio, aiohttp, feedparser

**Documentation:** [firefeed-rss-parser/README.md](https://github.com/firefeed-net/firefeed-rss-parser/blob/main/README.md)

### 3. FireFeed Telegram Bot ([firefeed-telegram-bot](https://github.com/firefeed-net/firefeed-telegram-bot.git))

Telegram bot for user interaction and news notifications.

**Key Features:**
- Personalized news delivery
- Category-based subscriptions
- Multilingual interface (EN, RU, DE, FR)
- Automatic news publishing to channels
- Rate limiting and spam prevention
- User management and preferences

**Tech Stack:** aiogram, Redis, PostgreSQL

**Documentation:** [firefeed-telegram-bot/README.md](https://github.com/firefeed-net/firefeed-telegram-bot/blob/main/README.md)

### Service Communication

Services communicate via HTTP REST APIs:

```
Telegram Bot ──► FireFeed API ◄── RSS Parser
     │                │                │
     │                │                │
     └────────────────┴────────────────┘
                      │
              ┌───────▼───────┐
              │   Database    │
              │   & Cache     │
              └───────────────┘
```

- **Telegram Bot** → **FireFeed API**: User data, subscriptions, RSS items
- **RSS Parser** → **FireFeed API**: Feed management, item storage
- **FireFeed API** → **Database**: Persistent storage
- **All Services** → **Redis**: Caching and session management

## Installation and Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 12+ with pgvector extension
- Redis 6+
- Docker & Docker Compose (recommended)
- Telegram Bot API token

### Quick Start with Docker Compose

The easiest way to run all services:

```bash
# Clone the repository with submodules
git clone --recurse-submodules https://github.com/firefeed-net/firefeed.git
cd firefeed

# Copy environment files
cp firefeed-api/.env.example firefeed-api/.env
cp firefeed-rss-parser/.env.example firefeed-rss-parser/.env
cp firefeed-telegram-bot/.env.example firefeed-telegram-bot/.env

# Edit .env files with your configuration
# Then start all services
docker-compose up -d
```

### Manual Installation

#### 1. FireFeed API

```bash
# Clone the API repository
git clone https://github.com/firefeed-net/firefeed-api.git
cd firefeed-api

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start the server
python -m firefeed-api.main
```

#### 2. FireFeed RSS Parser

```bash
# Clone the RSS Parser repository
git clone https://github.com/firefeed-net/firefeed-rss-parser.git
cd firefeed-rss-parser

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start the parser
python -m firefeed_rss_parser
```

#### 3. FireFeed Telegram Bot

```bash
# Clone the Telegram Bot repository
git clone https://github.com/firefeed-net/firefeed-telegram-bot.git
cd firefeed-telegram-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start the bot
python -m firefeed_telegram_bot
```

## Configuration

### Environment Variables

Each service has its own `.env.example` file with all available configuration options:

- [firefeed-api/.env.example](https://github.com/firefeed-net/firefeed-api/blob/main/.env.example) - API service configuration
- [firefeed-rss-parser/.env.example](https://github.com/firefeed-net/firefeed-rss-parser/blob/main/.env.example) - RSS parser configuration
- [firefeed-telegram-bot/.env.example](https://github.com/firefeed-net/firefeed-telegram-bot/blob/main/.env.example) - Telegram bot configuration

### Common Configuration

#### Database Configuration
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=firefeed
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
```

#### Redis Configuration
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
```

#### FireFeed API Configuration
```env
# For RSS Parser and Telegram Bot
FIREFEED_API_BASE_URL=http://localhost:8000
FIREFEED_API_KEY=your_api_key
```

### Optional AI Features Configuration

FireFeed provides optional AI-powered features that can be enabled or disabled:

#### TRANSLATION_ENABLED
- **Default**: `true`
- **Description**: Controls automatic translation of news articles to multiple languages
- **Impact**: When disabled, news items will only be available in their original language

#### DUPLICATE_DETECTOR_ENABLED
- **Default**: `true`
- **Description**: Controls ML-based duplicate detection using semantic analysis
- **Impact**: When disabled, all news items will be processed without duplicate checking

### AI Model Configuration

#### TRANSLATION_MODEL
- **Default**: `facebook/m2m100_418M`
- **Description**: Specifies the translation model from Hugging Face Transformers
- **Supported models**: M2M100, Helsinki-NLP OPUS-MT, MarianMT, MBart, etc.

#### EMBEDDING_SENTENCE_TRANSFORMER_MODEL
- **Default**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Description**: Sentence transformer model for generating text embeddings

#### SPACY_MODELS
- **Default**: `{"en": "en_core_web_sm", "ru": "ru_core_news_sm", "de": "de_core_news_sm", "fr": "fr_core_news_sm"}`
- **Description**: spaCy language models for text processing

### Systemd Services

For production environments, systemd services are recommended.

**FireFeed API Service** (`/etc/systemd/system/firefeed-api.service`):

```ini
[Unit]
Description=FireFeed API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=firefeed
WorkingDirectory=/opt/firefeed/firefeed-api
Environment=PATH=/opt/firefeed/venv/bin
ExecStart=/opt/firefeed/venv/bin/python -m firefeed-api.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**FireFeed RSS Parser Service** (`/etc/systemd/system/firefeed-rss-parser.service`):

```ini
[Unit]
Description=FireFeed RSS Parser Service
After=network.target firefeed-api.service

[Service]
Type=simple
User=firefeed
WorkingDirectory=/opt/firefeed/firefeed-rss-parser
Environment=PATH=/opt/firefeed/venv/bin
ExecStart=/opt/firefeed/venv/bin/python -m firefeed_rss_parser
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**FireFeed Telegram Bot Service** (`/etc/systemd/system/firefeed-telegram-bot.service`):

```ini
[Unit]
Description=FireFeed Telegram Bot Service
After=network.target firefeed-api.service

[Service]
Type=simple
User=firefeed
WorkingDirectory=/opt/firefeed/firefeed-telegram-bot
Environment=PATH=/opt/firefeed/venv/bin
ExecStart=/opt/firefeed/venv/bin/python -m firefeed_telegram_bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

Example configuration for proxying all services:

```nginx
upstream firefeed_api {
    server 127.0.0.1:8000;
}

upstream firefeed_rss_parser {
    server 127.0.0.1:8080;
}

upstream firefeed_telegram_bot {
    server 127.0.0.1:8081;
}

server {
    listen 80;
    server_name your_domain.com;

    # FireFeed API
    location /api/ {
        proxy_pass http://firefeed_api;
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

    # Telegram Webhook
    location /webhook {
        proxy_pass http://firefeed_telegram_bot/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # RSS Parser Metrics (optional, for monitoring)
    location /rss-parser/metrics {
        proxy_pass http://firefeed_rss_parser/metrics;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }

    # Telegram Bot Metrics (optional, for monitoring)
    location /telegram-bot/metrics {
        proxy_pass http://firefeed_telegram_bot/metrics;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }
}
```

## API Documentation

After starting the API server, documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### Public API (firefeed-api)
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/rss-items/` - Get RSS items
- `GET /api/v1/categories/` - Get categories
- `GET /api/v1/sources/` - Get sources

#### Internal API (firefeed-api)
- Internal endpoints for microservice communication
- Service-to-service authentication via API keys

## Development

### Development Setup

```bash
# Clone repository with submodules
git clone --recurse-submodules https://github.com/firefeed-net/firefeed.git
cd firefeed

# Setup each service
cd firefeed-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

cd firefeed-rss-parser
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

cd firefeed-telegram-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### Running Tests

Each service has its own test suite:

```bash
# FireFeed API tests
cd firefeed-api
pytest tests/

# FireFeed RSS Parser tests
cd firefeed-rss-parser
pytest tests/

# FireFeed Telegram Bot tests
cd firefeed-telegram-bot
pytest tests/
```

### Code Style

The project uses `ruff` for linting and formatting:

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Type checking
mypy .
```

## Project Structure

```
firefeed/
├── firefeed-api/              # REST API service (submodule)
│   ├── routers/              # API endpoints
│   ├── services/             # Business logic
│   ├── models/               # Data models
│   ├── database/             # Database utilities
│   ├── config/               # Configuration
│   ├── monitoring/           # Health checks & metrics
│   └── tests/                # Test suite
│
├── firefeed-rss-parser/       # RSS parsing service (submodule)
│   ├── services/             # Parsing logic
│   ├── models/               # Data models
│   ├── config/               # Configuration
│   ├── docs/                 # Documentation
│   └── tests/                # Test suite
│
├── firefeed-telegram-bot/     # Telegram bot service (submodule)
│   ├── handlers/             # Bot command handlers
│   ├── services/             # Business logic
│   ├── models/               # Data models
│   ├── config/               # Configuration
│   ├── monitoring/           # Health checks & metrics
│   └── tests/                # Test suite
│
├── docker-compose.yml         # Docker orchestration
├── CODE_OF_CONDUCT.md         # Code of conduct
├── CONTRIBUTING.md            # Contributing guidelines
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Monitoring

Each service provides health checks and Prometheus metrics:

- **FireFeed API**: `http://localhost:8000/health`, `http://localhost:8000/metrics`
- **RSS Parser**: `http://localhost:8081/health`, `http://localhost:8080/metrics`
- **Telegram Bot**: `http://localhost:8081/health`, `http://localhost:8080/metrics`

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contributing Steps

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Website**: https://firefeed.net
- **GitHub Issues**: https://github.com/firefeed-net/firefeed/issues
- **Email**: mail@firefeed.net