import asyncio
import sys
import os
import logging
import traceback

# Add project root to module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.email_service.sender import send_verification_email

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_email():
    # Replace with your email for testing
    test_email = "yurem@bk.ru"  # <-- test email
    verification_code = "123456"

    logger.info(f"Sending test email to {test_email}")
    logger.info(f"Verification code: {verification_code}")

    # Test sending in different languages
    for language in ["en", "ru", "de"]:
        logger.info(f"Testing sending in language: {language}")
        try:
            success = await send_verification_email(test_email, verification_code, language)
            if success:
                logger.info(f"✅ Email in {language} sent successfully!")
            else:
                logger.error(f"❌ Error sending email in {language}")
        except Exception as e:
            logger.error(f"❌ Exception sending email in {language}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

    logger.info("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_email())
