import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default logging level, overridable via env var
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")


def setup_logging():
    """Global logging setup for the entire application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),  # Convert string to level
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # Output to stderr for systemd/journalctl
        ],
    )
