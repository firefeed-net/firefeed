import asyncio
import logging
from di_container import setup_di_container, get_service
from interfaces import ITranslationService

logger = logging.getLogger(__name__)


async def test_translations():
    # Initialize DI container
    setup_di_container()

    # Get TranslationService via DI
    translator = get_service(ITranslationService)

    # Examples from logs - short texts
    test_cases = [
        ("OpenAI, AMD Announce Massive Computing Deal, Marking New Phase of AI Boom", "en", "ru"),
        (
            "The five-year agreement will challenge Nvidia's market dominance and gives OpenAI 10% of AMD if it hits milestones for chip deployment.",
            "en",
            "ru",
        ),
    ]

    # Long texts for testing
    long_test_cases = [
        (
            "OpenAI and AMD have announced a massive computing deal that marks a new phase in the AI boom. This partnership will bring significant changes to the industry and challenge existing market leaders like Nvidia. The agreement includes substantial investments in chip manufacturing and AI infrastructure development.",
            "en",
            "ru",
        ),
        (
            "The five-year agreement between OpenAI and AMD represents a major shift in the AI hardware landscape. This deal will challenge Nvidia's market dominance and provide OpenAI with access to AMD's advanced chip technologies. The partnership includes equity stakes and milestone-based payments that could reach billions of dollars over the contract period.",
            "en",
            "ru",
        ),
    ]

    logger.info("=== TESTING SHORT TEXTS ===")
    for text, src, tgt in test_cases:
        logger.info(f"Testing: '{text}' {src} -> {tgt}")
        try:
            result = await translator.translate_async([text], src, tgt)
            logger.info(f"Result: '{result[0]}'")
        except Exception as e:
            logger.error(f"Error: {e}")

    logger.info("=== TESTING LONG TEXTS ===")
    for text, src, tgt in long_test_cases:
        logger.info(f"Testing long text ({len(text)} characters): '{text[:100]}...' {src} -> {tgt}")
        try:
            result = await translator.translate_async([text], src, tgt)
            logger.info(f"Result: '{result[0][:200]}...'")
        except Exception as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_translations())
