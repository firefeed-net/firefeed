# telegram_bot/handlers/error_handlers.py - Error handlers
import logging

from telegram.error import NetworkError, BadRequest
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Error handler."""
    if isinstance(context.error, NetworkError):
        logger.error("Network error detected. Retrying...")
    elif isinstance(context.error, BadRequest):
        if "Query is too old" in str(context.error):
            logger.error("Ignoring outdated callback query")
            return
        else:
            logger.error(f"Bad request error: {context.error}")
    else:
        logger.error(f"Other error: {context.error}")