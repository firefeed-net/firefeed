import asyncio
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import NetworkError, BadRequest

from .di_container import DIContainer
from .utils.retry_decorator import retry_on_failure

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


def main():
    logger.info("=== TELEGRAM BOT STARTUP BEGINNING ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")

    # Initialize DI container
    container = DIContainer()
    asyncio.run(container.initialize())

    bot_token = container.get_singleton('bot_token')
    if not bot_token:
        logger.error("Bot token not configured")
        return

    logger.info("Bot token configured: Yes")

    application = Application.builder().token(bot_token).post_stop(container.shutdown).post_init(container._initialize_http_session).build()

    # Get services
    bot_service = container.bot_service
    scheduler_service = container.scheduler_service

    # Add handlers
    application.add_handler(CommandHandler("start", bot_service.start_command))
    application.add_handler(CommandHandler("settings", bot_service.settings_command))
    application.add_handler(CommandHandler("help", bot_service.help_command))
    application.add_handler(CommandHandler("status", bot_service.status_command))
    application.add_handler(CommandHandler("link", bot_service.link_telegram_command))
    application.add_handler(CallbackQueryHandler(bot_service.button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_service.handle_menu_selection))
    application.add_handler(MessageHandler(filters.ALL, bot_service.debug))
    application.add_error_handler(error_handler)

    # Add job queue tasks
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(scheduler_service.monitor_rss_items_task, interval=180, first=1, job_kwargs={"misfire_grace_time": 600})
        job_queue.run_repeating(scheduler_service.cleanup_expired_user_data, interval=3600, first=60)
        logger.info("Registered RSS items monitoring task (every 3 minutes)")
        logger.info("Registered task to clean expired user data (every 60 minutes)")

    logger.info("Bot started in Webhook mode")
    try:
        webhook_config = container.get_singleton('webhook_config')  # Assuming it's set
        application.run_webhook(**webhook_config, close_loop=False)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interrupted by user or system...")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()