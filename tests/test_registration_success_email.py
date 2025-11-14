import asyncio
import sys
import os
import logging
import traceback

# Add project root to module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.email_service.sender import send_registration_success_email

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_registration_success_email():
    # Replace with your email for testing
    test_email = "yurem@bk.ru"  # <-- test email

    logger.info(f"Sending test registration success email to {test_email}")

    # Test sending in different languages
    for language in ["en", "ru", "de"]:
        logger.info(f"Testing sending in language: {language}")
        try:
            success = await send_registration_success_email(test_email, language)
            if success:
                logger.info(f"✅ Registration success email in {language} sent successfully!")
            else:
                logger.error(f"❌ Error sending registration success email in {language}")
        except Exception as e:
            logger.error(f"❌ Exception sending registration success email in {language}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

    logger.info("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_registration_success_email())