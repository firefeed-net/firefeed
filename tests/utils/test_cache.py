import pytest
from unittest.mock import patch, MagicMock
from utils.cache import SpacyModelCache


class TestSpacyModelCache:
    def test_init_default(self):
        """Test initialization with default parameters"""
        cache = SpacyModelCache()
        assert cache.max_cache_size == 3
        assert cache.models == {}
        assert cache.usage_order == []

    def test_init_custom_size(self):
        """Test initialization with custom cache size"""
        cache = SpacyModelCache(max_cache_size=5)
        assert cache.max_cache_size == 5

    @patch('utils.cache.get_service_config')
    def test_get_model_cached(self, mock_config):
        """Test getting cached model"""
        cache = SpacyModelCache()
        mock_model = MagicMock()
        cache.models['en'] = mock_model
        cache.usage_order = ['en']

        result = cache.get_model('en')

        assert result == mock_model
        assert cache.usage_order == ['en']  # Should be at the end
        mock_config.assert_not_called()

    @patch('utils.cache.get_service_config')
    def test_get_model_cached_reorder(self, mock_config):
        """Test getting cached model reorders usage"""
        cache = SpacyModelCache()
        mock_model = MagicMock()
        cache.models = {'en': mock_model, 'ru': MagicMock()}
        cache.usage_order = ['ru', 'en']  # en was used before ru

        result = cache.get_model('en')

        assert result == mock_model
        assert cache.usage_order == ['ru', 'en']  # en moved to end

    @patch('utils.cache.spacy.load')
    @patch('utils.cache.get_service_config')
    def test_get_model_load_success(self, mock_config, mock_spacy_load):
        """Test loading new model successfully"""
        cache = SpacyModelCache()
        mock_model = MagicMock()
        mock_spacy_load.return_value = mock_model

        # Mock config
        mock_config_obj = MagicMock()
        mock_config_obj.deduplication.spacy_models.en_model = 'en_core_web_sm'
        mock_config.return_value = mock_config_obj

        result = cache.get_model('en')

        assert result == mock_model
        assert 'en' in cache.models
        assert cache.usage_order == ['en']
        mock_spacy_load.assert_called_once_with('en_core_web_sm')

    @patch('utils.cache.spacy.load')
    @patch('utils.cache.get_service_config')
    def test_get_model_unknown_language(self, mock_config, mock_spacy_load):
        """Test loading model for unknown language falls back to en_core_web_sm"""
        cache = SpacyModelCache()
        mock_model = MagicMock()
        mock_spacy_load.return_value = mock_model

        # Mock config without the language
        mock_config_obj = MagicMock()
        mock_config_obj.deduplication.spacy_models.en_model = 'en_core_web_sm'
        mock_config.return_value = mock_config_obj

        result = cache.get_model('xx')  # Unknown language

        assert result == mock_model
        mock_spacy_load.assert_called_once_with('en_core_web_sm')

    @patch('utils.cache.spacy.load')
    @patch('utils.cache.get_service_config')
    def test_get_model_cache_eviction(self, mock_config, mock_spacy_load):
        """Test cache eviction when limit exceeded"""
        cache = SpacyModelCache(max_cache_size=2)
        mock_model1 = MagicMock()
        mock_model2 = MagicMock()
        mock_model3 = MagicMock()
        mock_spacy_load.side_effect = [mock_model1, mock_model2, mock_model3]

        # Mock config
        mock_config_obj = MagicMock()
        mock_config_obj.deduplication.spacy_models.en_model = 'en_core_web_sm'
        mock_config_obj.deduplication.spacy_models.ru_model = 'ru_core_news_sm'
        mock_config_obj.deduplication.spacy_models.de_model = 'de_core_news_sm'
        mock_config.return_value = mock_config_obj

        # Load first model
        cache.get_model('en')
        assert len(cache.models) == 1
        assert cache.usage_order == ['en']

        # Load second model
        cache.get_model('ru')
        assert len(cache.models) == 2
        assert cache.usage_order == ['en', 'ru']

        # Load third model - should evict oldest (en)
        cache.get_model('de')
        assert len(cache.models) == 2
        assert 'en' not in cache.models
        assert cache.usage_order == ['ru', 'de']

    @patch('utils.cache.spacy.load')
    @patch('utils.cache.get_service_config')
    def test_get_model_load_failure(self, mock_config, mock_spacy_load):
        """Test model loading failure"""
        cache = SpacyModelCache()
        mock_spacy_load.side_effect = OSError("Model not found")

        # Mock config
        mock_config_obj = MagicMock()
        mock_config_obj.deduplication.spacy_models.en_model = 'en_core_web_sm'
        mock_config.return_value = mock_config_obj

        result = cache.get_model('en')

        assert result is None
        assert 'en' not in cache.models
        assert cache.usage_order == []


    def test_cleanup(self):
        """Test cache cleanup"""
        cache = SpacyModelCache()
        cache.models = {'en': MagicMock(), 'ru': MagicMock()}
        cache.usage_order = ['en', 'ru']

        cache.cleanup()

        assert cache.models == {}
        assert cache.usage_order == []

    @patch('utils.cache.spacy.load')
    @patch('utils.cache.get_service_config')
    def test_get_model_all_languages(self, mock_config, mock_spacy_load):
        """Test loading models for all supported languages"""
        cache = SpacyModelCache()
        mock_model = MagicMock()
        mock_spacy_load.return_value = mock_model

        # Mock config with all models
        mock_config_obj = MagicMock()
        mock_config_obj.deduplication.spacy_models.en_model = 'en_core_web_sm'
        mock_config_obj.deduplication.spacy_models.ru_model = 'ru_core_news_sm'
        mock_config_obj.deduplication.spacy_models.de_model = 'de_core_news_sm'
        mock_config_obj.deduplication.spacy_models.fr_model = 'fr_core_news_sm'
        mock_config.return_value = mock_config_obj

        languages = ['en', 'ru', 'de', 'fr']

        for lang in languages:
            result = cache.get_model(lang)
            assert result == mock_model
            assert lang in cache.models

        # Verify correct models were loaded
        expected_calls = [
            'en_core_web_sm',
            'ru_core_news_sm',
            'de_core_news_sm',
            'fr_core_news_sm'
        ]
        actual_calls = [call[0][0] for call in mock_spacy_load.call_args_list]
        assert actual_calls == expected_calls