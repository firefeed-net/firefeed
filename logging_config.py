import logging
import sys
from config import LOG_LEVEL


def setup_logging():
    """Global logging setup for the entire application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),  # Convert string to level
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # Output to stderr for systemd/journalctl
        ],
    )
