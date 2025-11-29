# telegram_bot/bot.py - Main bot application
#
# Required environment variables:
# - BOT_TOKEN: Telegram bot token from @BotFather
# - WEBHOOK_URL: Public URL for webhook (e.g., https://yourdomain.com/webhook)
#
# Optional environment variables:
# - BOT_API_KEY: API key for bot authentication with the main API
# - WEBHOOK_LISTEN: IP address to listen on (default: 127.0.0.1)
# - WEBHOOK_PORT: Port to listen on (default: 5000)
# - WEBHOOK_URL_PATH: Webhook path (default: webhook)
import asyncio
import logging
import os
import sys
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from telegram_bot.config import BOT_TOKEN, WEBHOOK_CONFIG
from logging_config import setup_logging
from telegram_bot.services.user_state_service import initialize_user_manager, cleanup_expired_data
from telegram_bot.services.api_service import close_http_session
from telegram_bot.handlers.command_handlers import (
    start_command, settings_command, help_command, status_command,
    change_language_command, link_telegram_command
)
from telegram_bot.handlers.callback_handlers import button_handler
from telegram_bot.handlers.message_handlers import handle_menu_selection, debug
from telegram_bot.handlers.error_handlers import error_handler
from telegram_bot.services.rss_service import monitor_rss_items_task

# Logging setup
setup_logging()
logger = logging.getLogger(__name__)


async def post_stop(application) -> None:
    """Called when application stops."""
    logger.info("Stopping application and closing resources...")

    await close_http_session()

    try:
        from config import close_shared_db_pool
        await close_shared_db_pool()
        logger.info("Shared connection pool closed")
    except Exception as e:
        logger.error(f"Error closing shared pool: {e}")

    logger.info("All resources freed")


async def post_init(application) -> None:
    """Called after application initialization."""
    logger.info("Application initialized, initializing bot components...")

    # Initialize user_manager
    try:
        await initialize_user_manager()
        logger.info("UserManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize UserManager: {e}")
        logger.warning("Bot will work without user management features")


def main():
    logger.info("=== BOT STARTUP BEGINNING ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Bot token configured: {'Yes' if BOT_TOKEN else 'No'}")

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        logger.error("Please set BOT_TOKEN in your environment variables.")
        logger.error("Get your bot token from https://t.me/Botfather")
        sys.exit(1)

    if not WEBHOOK_CONFIG.get("webhook_url"):
        logger.error("WEBHOOK_URL environment variable is not set!")
        logger.error("Please set WEBHOOK_URL in your environment variables.")
        logger.error("This should be the public URL where your bot can receive updates.")
        sys.exit(1)

    application = Application.builder().token(BOT_TOKEN).post_stop(post_stop).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("link", link_telegram_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_selection))
    application.add_handler(MessageHandler(filters.ALL, debug))
    application.add_error_handler(error_handler)

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(monitor_rss_items_task, interval=180, first=10, job_kwargs={"misfire_grace_time": 600})  # Delay first run by 10 seconds
        job_queue.run_repeating(cleanup_expired_data, interval=3600, first=60)
        logger.info("Registered RSS items monitoring task (every 3 minutes, first run in 10 seconds)")
        logger.info("Registered task to clean expired user data (every 60 minutes)")

    logger.info("Bot started in Webhook mode")
    try:
        application.run_webhook(**WEBHOOK_CONFIG, close_loop=False)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interrupted by user or system...")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()