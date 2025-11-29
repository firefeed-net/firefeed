# Contributing Guide to FireFeed

Thank you for your interest in the FireFeed project! We welcome contributions from the community.

## Ways to Contribute

### Reporting Bugs
If you find a bug, please:
1. Check if the bug has already been reported in Issues
2. Create a new Issue with a clear description:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Python and dependency versions
   - Error logs (if any)

### Suggesting New Features
For suggesting new features:
1. Describe the problem the feature solves
2. Suggest a specific implementation
3. Explain how this will improve the project
4. Specify priority (low/medium/high)

### Participating in Development
1. Choose an Issue from the "good first issue" list or discuss your idea
2. Report that you are working on the Issue
3. Follow the project's code standards

## Development Process

### Environment Setup
```bash
# Clone the repository from GitHub
git clone https://github.com/yuremweiland/firefeed.git
# or GitVerse
git clone https://gitverse.ru/yuryweiland/firefeed.git
cd firefeed

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Creating a Branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description

### Code Standards

- Follow PEP 8 for Python code
- Use type hints for all new functions
- Write docstrings for all public methods
- Add tests for new functionality

### Commits

Use clear commit messages:

```
feat: add support for new RSS sources
fix: fix memory leak in translator
docs: update API documentation
test: add tests for parser
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Check code style
flake8 .
black --check .
mypy .
```

### Creating a Pull Request

1. Update your branch with main: git pull origin main
2. Make sure all tests pass
3. Create a PR with a description of changes
4. Specify related Issues
5. Wait for review from maintainers

### Project Structure

```
firefeed/
├── api/                        # FastAPI REST API
│   ├── routers/                # API endpoints organized by domain
│   ├── email_service/          # Email notification service
│   ├── app.py                  # FastAPI application setup
│   ├── main.py                 # API server entry point
│   ├── models.py               # Pydantic request/response models
│   ├── deps.py                 # Dependency injection for API
│   ├── database.py             # Database connection for API
│   ├── middleware.py           # Custom middleware (CORS, logging)
│   └── websocket.py            # WebSocket support for real-time features
├── services/                   # Service-oriented architecture
│   ├── rss/                    # RSS processing services
│   │   ├── rss_manager.py      # Main RSS processing orchestrator
│   │   ├── rss_fetcher.py      # RSS feed fetching and parsing
│   │   ├── rss_storage.py      # RSS data persistence
│   │   ├── rss_validator.py    # RSS feed validation
│   │   └── media_extractor.py  # Image/video extraction from RSS
│   ├── text_analysis/          # ML-powered text analysis
│   │   ├── duplicate_detector.py # Semantic duplicate detection
│   │   └── embeddings_processor.py # Text embeddings and preprocessing
│   ├── translation/            # Multilingual translation services
│   │   ├── translation_service.py # Core translation logic
│   │   ├── model_manager.py    # ML model lifecycle management
│   │   ├── task_queue.py       # Async translation task processing
│   │   ├── translation_cache.py # Translation result caching
│   │   ├── translations.py     # Localized UI messages
│   │   └── terminology_dict.py # Domain-specific translation terms
│   ├── database_pool_adapter.py # Database connection pooling
│   └── maintenance_service.py  # System maintenance tasks
├── tests/                      # Comprehensive test suite
│   ├── test_services.py        # Service layer testing
│   ├── test_rss_manager.py     # RSS functionality testing
│   ├── test_api_keys.py        # API authentication testing
│   ├── test_bot.py             # Telegram bot testing
│   ├── test_database.py        # Database operations testing
│   ├── test_email.py           # Email service testing
│   └── test_utils.py           # Utility function testing
├── utils/                      # Shared utility functions
│   ├── text.py                 # Text processing utilities
│   ├── image.py                # Image manipulation utilities
│   ├── video.py                # Video processing utilities
│   ├── api.py                  # API client utilities
│   ├── cache.py                # Caching abstractions
│   ├── database.py             # Database helper functions
│   ├── retry.py                # Retry mechanisms
│   └── cleanup.py              # Resource cleanup utilities
├── bot.py                      # Telegram bot main application
├── config.py                   # Application constants and settings
├── config_services.py          # Environment-based service configuration
├── di_container.py             # Dependency injection container
├── exceptions.py               # Custom exception hierarchy
├── interfaces.py               # Abstract service interfaces
├── logging_config.py           # Centralized logging configuration
├── main.py                     # Application entry point
├── rss_parser.py               # Legacy RSS parser (being phased out)
├── user_manager.py             # User account management
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── docker-compose.yml          # Multi-container Docker setup
├── Dockerfile                  # Container build instructions
├── run_api.sh                  # API server startup script
├── run_bot.sh                  # Bot startup script
└── run_parser.sh               # RSS parser startup script
```

## Contacts

For development questions:

- Create an Issue in GitHub
- Mention @yuremweiland for urgent questions

Thank you for your contribution!
