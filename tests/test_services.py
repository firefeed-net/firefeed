# tests/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from di_container import DIContainer, get_service
from interfaces import IRSSFetcher, IRSSValidator, IRSSStorage, IMediaExtractor, ITranslationService
from apps.rss_parser.services import RSSFetcher, RSSValidator, RSSStorage, MediaExtractor
from services.translation import TranslationService, TranslationCache


class TestDIContainer:
    """Test dependency injection container"""

    def test_register_and_resolve(self):
        """Test basic registration and resolution"""
        container = DIContainer()

        # Register a mock service
        mock_service = MagicMock()
        container.register_instance(str, mock_service)

        # Resolve it
        resolved = container.resolve(str)
        assert resolved == mock_service

    def test_register_factory(self):
        """Test factory registration"""
        container = DIContainer()

        def factory():
            return "test"

        container.register_factory(str, factory)
        resolved = container.resolve(str)
        assert resolved == "test"


class TestRSSServices:
    """Test RSS services"""

    @pytest.fixture
    def mock_media_extractor(self):
        """Mock media extractor"""
        extractor = MagicMock(spec=IMediaExtractor)
        extractor.extract_image = AsyncMock(return_value="http://example.com/image.jpg")
        extractor.extract_video = AsyncMock(return_value=None)
        return extractor

    @pytest.fixture
    def mock_duplicate_detector(self):
        """Mock duplicate detector"""
        detector = MagicMock()
        detector.is_duplicate.return_value = (False, {})
        return detector

    def test_rss_fetcher_creation(self, mock_media_extractor, mock_duplicate_detector):
        """Test RSS fetcher can be created"""
        fetcher = RSSFetcher(mock_media_extractor, mock_duplicate_detector)
        assert fetcher.media_extractor == mock_media_extractor
        assert fetcher.duplicate_detector == mock_duplicate_detector

    def test_generate_news_id(self, mock_media_extractor, mock_duplicate_detector):
        """Test news ID generation"""
        fetcher = RSSFetcher(mock_media_extractor, mock_duplicate_detector)
        news_id = fetcher.generate_news_id("Title", "Content", "http://link.com", 1)
        assert isinstance(news_id, str)
        assert len(news_id) == 64  # SHA256 hex length

    async def test_check_for_duplicates(self, mock_media_extractor, mock_duplicate_detector):
        """Test duplicate checking"""
        fetcher = RSSFetcher(mock_media_extractor, mock_duplicate_detector)
        result = await fetcher.check_for_duplicates("Title", "Content", "http://link.com", "en")
        assert result is False
        mock_duplicate_detector.is_duplicate.assert_called_once()


class TestTranslationServices:
    """Test translation services"""

    @pytest.fixture
    def mock_model_manager(self):
        """Mock model manager"""
        manager = MagicMock()
        manager.get_model.return_value = (MagicMock(), MagicMock())
        return manager

    @pytest.fixture
    def mock_translator_queue(self):
        """Mock translator queue"""
        queue = MagicMock()
        return queue

    def test_translation_service_creation(self, mock_model_manager, mock_translator_queue):
        """Test translation service can be created"""
        service = TranslationService(mock_model_manager, mock_translator_queue)
        assert service.model_manager == mock_model_manager
        assert service.translator_queue == mock_translator_queue

    def test_translation_cache_creation(self):
        """Test translation cache can be created"""
        cache = TranslationCache()
        assert cache.cache_ttl == 3600  # default TTL
        assert cache.max_cache_size == 10000

    async def test_short_text_translation(self):
        """Test translation of short texts"""
        from di_container import setup_di_container, get_service
        from interfaces import ITranslationService

        # Initialize DI container
        setup_di_container()

        # Get TranslationService via DI
        translator = get_service(ITranslationService)

        test_cases = [
            ("OpenAI, AMD Announce Massive Computing Deal, Marking New Phase of AI Boom", "en", "ru"),
            (
                "The five-year agreement will challenge Nvidia's market dominance and gives OpenAI 10% of AMD if it hits milestones for chip deployment.",
                "en",
                "ru",
            ),
        ]

        for text, src, tgt in test_cases:
            result = await translator.translate_async([text], src, tgt)
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], str)
            assert len(result[0]) > 0

    async def test_long_text_translation(self):
        """Test translation of long texts"""
        from di_container import setup_di_container, get_service
        from interfaces import ITranslationService

        # Initialize DI container
        setup_di_container()

        # Get TranslationService via DI
        translator = get_service(ITranslationService)

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

        for text, src, tgt in long_test_cases:
            result = await translator.translate_async([text], src, tgt)
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], str)
            assert len(result[0]) > 0


class TestMediaExtractor:
    """Test media extractor"""

    async def test_extract_image_from_rss_item(self):
        """Test image extraction from RSS item"""
        extractor = MediaExtractor()

        # Test with media_thumbnail
        item = {"media_thumbnail": [{"url": "http://example.com/image.jpg"}]}
        result = await extractor.extract_image(item)
        assert result == "http://example.com/image.jpg"

        # Test with enclosure
        item = {"enclosures": [{"type": "image/jpeg", "href": "http://example.com/image2.jpg"}]}
        result = await extractor.extract_image(item)
        assert result == "http://example.com/image2.jpg"

        # Test no image
        item = {"title": "Test"}
        result = await extractor.extract_image(item)
        assert result is None

    async def test_extract_video_from_rss_item(self):
        """Test video extraction from RSS item"""
        extractor = MediaExtractor()

        # Test with enclosure
        item = {"enclosures": [{"type": "video/mp4", "href": "http://example.com/video.mp4"}]}
        result = await extractor.extract_video(item)
        assert result == "http://example.com/video.mp4"

        # Test no video
        item = {"title": "Test"}
        result = await extractor.extract_video(item)
        assert result is None


class TestIntegration:
    """Integration tests for service interactions"""

    async def test_service_dependencies(self):
        """Test that services can be instantiated with their dependencies"""
        # This test verifies that the service constructors work
        # In a real scenario, we'd use mocks for all dependencies

        # For now, just test that classes can be imported and have correct interfaces
        assert hasattr(RSSFetcher, 'fetch_feed')
        assert hasattr(RSSFetcher, 'fetch_feeds')
        assert hasattr(TranslationService, 'translate_async')
        assert hasattr(TranslationService, 'prepare_translations')
        assert hasattr(MediaExtractor, 'extract_image')
        assert hasattr(MediaExtractor, 'extract_video')