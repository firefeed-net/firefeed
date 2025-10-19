import asyncio
import sys
import os
import logging

# Добавляем корень проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_service.sender import send_verification_email

logger = logging.getLogger(__name__)

async def test_email():
    # Замени на свой email для тестирования
    test_email = "yurem@bk.ru"  # <-- Замени на реальный email
    verification_code = "123456"
    
    logger.info(f"Отправляем тестовое письмо на {test_email}")
    logger.info(f"Код подтверждения: {verification_code}")

    # Тестируем отправку на разных языках
    for language in ['en', 'ru', 'de']:
        logger.info(f"Тестируем отправку на языке: {language}")
        success = await send_verification_email(test_email, verification_code, language)
        if success:
            logger.info(f"✅ Письмо на {language} успешно отправлено!")
        else:
            logger.error(f"❌ Ошибка при отправке письма на {language}")

    logger.info("Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_email())