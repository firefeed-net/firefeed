import asyncio
from firefeed_translator import FireFeedTranslator

async def test_translations():
    translator = FireFeedTranslator(device="cpu", max_workers=2, max_concurrent_translations=1)

    # Примеры из логов - короткие тексты
    test_cases = [
        ("OpenAI, AMD Announce Massive Computing Deal, Marking New Phase of AI Boom", "en", "ru"),
        ("The five-year agreement will challenge Nvidia's market dominance and gives OpenAI 10% of AMD if it hits milestones for chip deployment.", "en", "ru")
    ]

    # Длинные тексты для тестирования
    long_test_cases = [
        ("OpenAI and AMD have announced a massive computing deal that marks a new phase in the AI boom. This partnership will bring significant changes to the industry and challenge existing market leaders like Nvidia. The agreement includes substantial investments in chip manufacturing and AI infrastructure development.", "en", "ru"),
        ("The five-year agreement between OpenAI and AMD represents a major shift in the AI hardware landscape. This deal will challenge Nvidia's market dominance and provide OpenAI with access to AMD's advanced chip technologies. The partnership includes equity stakes and milestone-based payments that could reach billions of dollars over the contract period.", "en", "ru")
    ]

    print("\n=== ТЕСТИРОВАНИЕ КОРОТКИХ ТЕКСТОВ ===")
    for text, src, tgt in test_cases:
        print(f"\nТестируем: '{text}' {src} -> {tgt}")
        try:
            result = await translator.translate_async([text], src, tgt)
            print(f"Результат: '{result[0]}'")
        except Exception as e:
            print(f"Ошибка: {e}")

    print("\n=== ТЕСТИРОВАНИЕ ДЛИННЫХ ТЕКСТОВ ===")
    for text, src, tgt in long_test_cases:
        print(f"\nТестируем длинный текст ({len(text)} символов): '{text[:100]}...' {src} -> {tgt}")
        try:
            result = await translator.translate_async([text], src, tgt)
            print(f"Результат: '{result[0][:200]}...'")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_translations())