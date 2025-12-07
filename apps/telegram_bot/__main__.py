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

from di_container import get_service
from config.logging_config import setup_logging
from config.services_config import get_service_config
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
from telegram_bot.services.telegram_service import cleanup_old_user_send_locks

# Logging setup
setup_logging()

# Load environment variables
import dotenv
dotenv.load_dotenv()

# Setup DI container
import asyncio
from di_container import setup_di_container
asyncio.run(setup_di_container())

logger = logging.getLogger(__name__)


async def post_stop(application) -> None:
    """Called when application stops."""
    logger.info("Stopping application and closing resources...")

    await close_http_session()

    try:
        # Close database pool via DI
        from di_container import get_service
        from interfaces import IDatabasePool
        db_pool_adapter = get_service(IDatabasePool)
        await db_pool_adapter.close()
        logger.info("Shared connection pool closed")
    except Exception as e:
        logger.error(f"Error closing shared pool: {e}")

    logger.info("All resources freed")


def main():
    logger.info("=== BOT STARTUP BEGINNING ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    # Get bot configuration from DI
    config_obj = get_service(dict)
    bot_token = config_obj.get('BOT_TOKEN')
    webhook_config = config_obj.get('WEBHOOK_CONFIG', {})

    logger.info(f"Bot token configured: {'Yes' if bot_token else 'No'}")

    if not bot_token:
        logger.error("BOT_TOKEN environment variable is not set!")
        logger.error("Please set BOT_TOKEN in your environment variables.")
        logger.error("Get your bot token from https://t.me/Botfather")
        sys.exit(1)

    if not webhook_config.get("webhook_url"):
        logger.error("WEBHOOK_URL environment variable is not set!")
        logger.error("Please set WEBHOOK_URL in your environment variables.")
        logger.error("This should be the public URL where your bot can receive updates.")
        sys.exit(1)

    application = Application.builder().token(bot_token).post_stop(post_stop).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("link", link_telegram_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_selection))
    application.add_handler(MessageHandler(filters.ALL, debug))
    application.add_error_handler(error_handler)

    # Get bot configuration
    config = get_service_config()

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_once(initialize_user_manager, when=0)  # Initialize telegram_user_service immediately in the event loop
        job_queue.run_repeating(
            monitor_rss_items_task,
            interval=config.telegram_bot.rss_monitor_interval,
            first=config.telegram_bot.rss_monitor_first_delay,
            job_kwargs={"misfire_grace_time": config.telegram_bot.rss_monitor_misfire_grace_time}
        )
        job_queue.run_repeating(
            cleanup_expired_data,
            interval=config.telegram_bot.user_cleanup_interval,
            first=config.telegram_bot.user_cleanup_first_delay
        )
        job_queue.run_repeating(
            cleanup_old_user_send_locks,
            interval=config.telegram_bot.send_locks_cleanup_interval,
            first=config.telegram_bot.send_locks_cleanup_first_delay
        )
        logger.info("Registered TelegramUserService initialization task (immediate)")
        logger.info(f"Registered RSS items monitoring task (every {config.telegram_bot.rss_monitor_interval} seconds, first run in {config.telegram_bot.rss_monitor_first_delay} seconds)")
        logger.info(f"Registered task to clean expired user data (every {config.telegram_bot.user_cleanup_interval} seconds)")
        logger.info(f"Registered task to clean old user send locks (every {config.telegram_bot.send_locks_cleanup_interval} seconds, first run in {config.telegram_bot.send_locks_cleanup_first_delay} seconds)")

    logger.info("Bot started in Webhook mode")
    try:
        application.run_webhook(**webhook_config)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interrupted by user or system...")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()