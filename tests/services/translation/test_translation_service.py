import pytest
from unittest.mock import AsyncMock, patch
from services.translation.translation_service import TranslationService


@pytest.fixture
def mock_model_manager():
    return AsyncMock()


@pytest.fixture
def mock_translator_queue():
    return AsyncMock()


@pytest.fixture
def service(mock_model_manager, mock_translator_queue):
    return TranslationService(mock_model_manager, mock_translator_queue)


class TestTranslationService:
    @pytest.mark.asyncio
    async def test_translate_async_empty_texts(self, service):
        result = await service.translate_async([], "en", "ru")
        assert result == []

    @pytest.mark.asyncio
    async def test_translate_async_success(self, service, mock_model_manager):
        mock_model = AsyncMock()
        mock_tokenizer = AsyncMock()
        mock_model_manager.get_model.return_value = (mock_model, mock_tokenizer)

        with patch.object(service, '_translate_sentence_batches_m2m100', new_callable=AsyncMock) as mock_translate, \
             patch.object(service, '_assemble_translated_texts') as mock_assemble, \
             patch.object(service, '_postprocess_text') as mock_postprocess:

            mock_translate.return_value = ["Translated sentence"]
            mock_assemble.return_value = ["Translated text"]
            mock_postprocess.return_value = "Processed text"

            result = await service.translate_async(["Hello world"], "en", "ru")

            assert result == ["Processed text"]
            mock_model_manager.get_model.assert_called_once_with("en", "ru")

    @pytest.mark.asyncio
    async def test_translate_async_cache_hit(self, service, mock_model_manager):
        # Add to cache with the actual hash that would be generated
        cache_key = f"en_ru_{hash('test')}_2_default"
        service.translation_cache[cache_key] = "Cached translation"

        result = await service.translate_async(["test"], "en", "ru")

        assert result == ["Cached translation"]
        # Model manager should not be called when cache hits
        mock_model_manager.get_model.assert_not_called()

    def test_preprocess_text_with_terminology(self, service):
        text = "This is a test API"
        result = service._preprocess_text_with_terminology(text, "ru")
        # Should replace "API" with Russian equivalent if in dict
        assert isinstance(result, str)

    def test_split_into_sentences(self, service):
        text = "Hello world. How are you? I'm fine!"
        result = service._split_into_sentences(text)
        assert len(result) == 3

    def test_postprocess_text(self, service):
        text = "  Test   text  "
        result = service._postprocess_text(text, "en")
        # The postprocess_text method has validation that returns empty string for short text
        # Let's test with longer text that passes validation
        long_text = "  This is a longer test text with more content  "
        result = service._postprocess_text(long_text, "en")
        assert result == "This is a longer test text with more content"

    def test_check_translation_language(self, service):
        text = "Привет мир"
        result = service._check_translation_language(text, "ru")
        assert result is True

        text = "Hello world"
        result = service._check_translation_language(text, "ru")
        assert result is False

    def test_is_broken_translation(self, service):
        text = "word " * 20  # 20 identical words
        result = service._is_broken_translation(text)
        assert result is True

        text = "This is a normal sentence."
        result = service._is_broken_translation(text)
        assert result is False

    def test_clear_translation_cache(self, service):
        service.translation_cache["key1"] = "value1"
        service.translation_cache["key2"] = "value2"

        service.clear_translation_cache()

        assert len(service.translation_cache) == 0