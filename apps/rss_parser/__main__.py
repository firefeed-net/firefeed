import asyncio
import sys
import logging
from config.logging_config import setup_logging
from di_container import setup_di_container
from apps.rss_parser.services.rss_parser import RSSParserService

setup_logging()
logger = logging.getLogger(__name__)


async def main():
    """Asynchronous entry point"""
    service = None
    try:
        await setup_di_container()
        service = RSSParserService()
        await service.start()
    except KeyboardInterrupt:
        logger.info("[RSS_PARSER] [MAIN] Service interrupted by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"[RSS_PARSER] [MAIN] Critical error in main loop: {e}")
        import traceback

        traceback.print_exc()
    # finally not needed, since cleanup is called inside start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[RSS_PARSER] [ENTRY] Application stopped by user")
    except Exception as e:
        logger.error(f"[RSS_PARSER] [ENTRY] Fatal application error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)