import asyncio
from firefeed_translator import FireFeedTranslator

async def test_translations():
    translator = FireFeedTranslator(device="cpu", max_workers=2, max_concurrent_translations=1)

    # Примеры из логов
    test_cases = [
        ("OpenAI, AMD Announce Massive Computing Deal, Marking New Phase of AI Boom", "en", "ru"),
        ("The five-year agreement will challenge Nvidia's market dominance and gives OpenAI 10% of AMD if it hits milestones for chip deployment.", "en", "ru"),
        ("technology", "en", "ru"),
        ("technology", "en", "de"),
    ]

    for text, src, tgt in test_cases:
        print(f"\nТестируем: '{text}' {src} -> {tgt}")
        try:
            result = await translator.translate_async([text], src, tgt)
            print(f"Результат: '{result[0]}'")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_translations())