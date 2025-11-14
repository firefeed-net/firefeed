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
├── api/                 # FastAPI application
├── tests/                 # Unit tests
├── bot.py              # Telegram bot
├── rss_parser.py       # RSS parser
├── firefeed_translator.py    # Translator
├── firefeed_dublicate_detector.py  # Duplicate detector
├── user_manager.py     # User manager
├── requirements.txt    # Dependencies
└── config/            # Configurations
```

## Contacts

For development questions:

- Create an Issue in GitHub
- Mention @yuremweiland for urgent questions

Thank you for your contribution!
