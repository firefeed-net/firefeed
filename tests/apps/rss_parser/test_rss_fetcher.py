import pytest
import asyncio
import hashlib
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from apps.rss_parser.services.rss_fetcher import RSSFetcher
from exceptions import RSSFetchError, RSSParseError, RSSValidationError


class MockMediaExtractor:
    """Mock media extractor for testing"""
    
    async def extract_image(self, entry):
        return "https://example.com/image.jpg"
    
    async def extract_video(self, entry):
        return "https://example.com/video.mp4"


class MockDuplicateDetector:
    """Mock duplicate detector for testing"""
    
    async def is_duplicate(self, title, content, link, lang):
        return False, {}


class TestRSSFetcher:
    """Test the RSSFetcher class"""
    
    def test_init(self):
        """Test RSSFetcher initialization"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        
        fetcher = RSSFetcher(media_extractor, duplicate_detector, max_concurrent_feeds=5, max_entries_per_feed=25)
        
        assert fetcher.media_extractor == media_extractor
        assert fetcher.duplicate_detector == duplicate_detector
        assert fetcher.max_entries_per_feed == 25
        assert isinstance(fetcher._feed_semaphore, asyncio.Semaphore)
        assert fetcher._feed_semaphore._value == 5
    
    def test_generate_news_id(self):
        """Test news ID generation"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        title = "Test Title"
        content = "Test content"
        link = "https://example.com/news"
        feed_id = 1
        
        news_id = fetcher.generate_news_id(title, content, link, feed_id)
        
        assert isinstance(news_id, str)
        assert len(news_id) == 64  # SHA256 hash length
        assert len(news_id.strip()) > 0
        
        # Same inputs should generate same ID
        news_id2 = fetcher.generate_news_id(title, content, link, feed_id)
        assert news_id == news_id2
    
    @pytest.mark.asyncio
    async def test_check_for_duplicates_disabled(self):
        """Test duplicate checking when disabled"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Mock config to disable duplicate detection
        with patch('apps.rss_parser.services.rss_fetcher.get_service_config') as mock_config:
            mock_config.return_value.deduplication.duplicate_detector_enabled = False
            
            result = await fetcher.check_for_duplicates("title", "content", "link", "en")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_for_duplicates_found(self):
        """Test duplicate checking when duplicate is found"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Mock config to enable duplicate detection
        with patch('apps.rss_parser.services.rss_fetcher.get_service_config') as mock_config:
            mock_config.return_value.deduplication.duplicate_detector_enabled = True
            
            # Mock duplicate detector to return True
            with patch.object(duplicate_detector, 'is_duplicate', return_value=(True, {"news_id": "duplicate_id"})):
                result = await fetcher.check_for_duplicates("title", "content", "link", "en")
                assert result is True
    
    @pytest.mark.asyncio
    async def test_check_for_duplicates_not_found(self):
        """Test duplicate checking when no duplicate is found"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Mock config to enable duplicate detection
        with patch('apps.rss_parser.services.rss_fetcher.get_service_config') as mock_config:
            mock_config.return_value.deduplication.duplicate_detector_enabled = True
            
            # Mock duplicate detector to return False
            with patch.object(duplicate_detector, 'is_duplicate', return_value=(False, {})):
                result = await fetcher.check_for_duplicates("title", "content", "link", "en")
                assert result is False
    
    @pytest.mark.asyncio
    async def test_check_for_duplicates_exception(self):
        """Test duplicate checking when exception occurs"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Mock config to enable duplicate detection
        with patch('apps.rss_parser.services.rss_fetcher.get_service_config') as mock_config:
            mock_config.return_value.deduplication.duplicate_detector_enabled = True
            
            # Mock duplicate detector to raise exception
            with patch.object(duplicate_detector, 'is_duplicate', side_effect=Exception("Duplicate detector error")):
                result = await fetcher.check_for_duplicates("title", "content", "link", "en")
                assert result is False  # Should return False on error
    
    @pytest.mark.asyncio
    async def test_fetch_feed(self):
        """Test fetching a single feed"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        feed_info = {
            "url": "https://example.com/feed.xml",
            "id": 1,
            "name": "Test Feed",
            "lang": "en",
            "category": "technology",
            "source": "TestSource"
        }
        headers = {"User-Agent": "TestAgent"}
        
        # Mock the internal fetch method
        with patch.object(fetcher, '_fetch_single_feed', return_value=[{"id": "item1"}]) as mock_fetch:
            result = await fetcher.fetch_feed(feed_info, headers)
            assert result == [{"id": "item1"}]
            mock_fetch.assert_called_once_with(feed_info, headers)
    
    @pytest.mark.asyncio
    async def test_fetch_feeds(self):
        """Test fetching multiple feeds"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        feeds_info = [
            {"url": "https://example.com/feed1.xml", "id": 1, "lang": "en", "category": "tech", "source": "Source1"},
            {"url": "https://example.com/feed2.xml", "id": 2, "lang": "en", "category": "tech", "source": "Source2"}
        ]
        headers = {"User-Agent": "TestAgent"}
        
        # Mock fetch_feed method
        with patch.object(fetcher, 'fetch_feed', side_effect=[[{"id": "item1"}], [{"id": "item2"}]]):
            results = await fetcher.fetch_feeds(feeds_info, headers)
            assert len(results) == 2
            assert results[0] == [{"id": "item1"}]
            assert results[1] == [{"id": "item2"}]
    
    @pytest.mark.asyncio
    async def test_fetch_feeds_with_exception(self):
        """Test fetching multiple feeds with one failing"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        feeds_info = [
            {"url": "https://example.com/feed1.xml", "id": 1, "lang": "en", "category": "tech", "source": "Source1"},
            {"url": "https://example.com/feed2.xml", "id": 2, "lang": "en", "category": "tech", "source": "Source2"}
        ]
        headers = {"User-Agent": "TestAgent"}
        
        # Mock fetch_feed method to raise exception for second feed
        async def mock_fetch_feed(feed_info, headers):
            if feed_info["id"] == 2:
                raise Exception("Feed fetch error")
            return [{"id": "item1"}]
        
        with patch.object(fetcher, 'fetch_feed', side_effect=mock_fetch_feed):
            results = await fetcher.fetch_feeds(feeds_info, headers)
            assert len(results) == 2
            assert results[0] == [{"id": "item1"}]
            assert isinstance(results[1], Exception)
    
    def test_extract_entry_title(self):
        """Test title extraction from RSS entry"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Test with title
        entry = MagicMock()
        entry.title = "  Test Title  "
        assert fetcher._extract_entry_title(entry) == "Test Title"
        
        # Test with empty title
        entry.title = ""
        assert fetcher._extract_entry_title(entry) == ""
        
        # Test with no title attribute
        delattr(entry, 'title')
        assert fetcher._extract_entry_title(entry) == ""
        
        # Test with non-string title
        entry.title = 123
        assert fetcher._extract_entry_title(entry) == "123"
    
    def test_extract_entry_content(self):
        """Test content extraction from RSS entry"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Test with content list
        entry = MagicMock()
        content_item = MagicMock()
        content_item.value = "Test content from list"
        entry.content = [content_item]
        assert fetcher._extract_entry_content(entry) == "Test content from list"
        
        # Test with content dict (not a list)
        entry2 = MagicMock()
        entry2.content = {"value": "Test content from dict"}
        assert fetcher._extract_entry_content(entry2) == "{'value': 'Test content from dict'}"
        
        # Test with summary (when content is falsy)
        entry3 = MagicMock()
        entry3.content = None
        entry3.summary = "Test summary"
        assert fetcher._extract_entry_content(entry3) == "Test summary"
        
        # Test with description (when content and summary are falsy)
        entry4 = MagicMock()
        entry4.content = None
        delattr(entry4, 'summary')
        entry4.description = "Test description"
        assert fetcher._extract_entry_content(entry4) == "Test description"
        
        # Test with no content fields
        entry5 = MagicMock()
        entry5.content = None
        delattr(entry5, 'summary')
        delattr(entry5, 'description')
        assert fetcher._extract_entry_content(entry5) == ""
    
    def test_extract_entry_link(self):
        """Test link extraction from RSS entry"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Test with direct link
        entry = MagicMock()
        entry.link = "https://example.com/news"
        assert fetcher._extract_entry_link(entry, "https://example.com/feed") == "https://example.com/news"
        
        # Test with relative link
        entry.link = "/relative/path"
        result = fetcher._extract_entry_link(entry, "https://example.com/feed")
        assert result == "https://example.com/relative/path"
        
        # Test with no link
        delattr(entry, 'link')
        entry.links = None
        assert fetcher._extract_entry_link(entry, "https://example.com/feed") == ""
        
        # Test with links list and alternate rel
        entry.links = [{"rel": "alternate", "href": "https://example.com/alt"}]
        assert fetcher._extract_entry_link(entry, "https://example.com/feed") == "https://example.com/alt"
        
        # Test with invalid URL (should raise RSSValidationError)
        entry.link = "javascript:alert('xss')"
        with pytest.raises(RSSValidationError):
            fetcher._extract_entry_link(entry, "https://example.com/feed")
    
    def test_extract_entry_published(self):
        """Test published date extraction from RSS entry"""
        media_extractor = MockMediaExtractor()
        duplicate_detector = MockDuplicateDetector()
        fetcher = RSSFetcher(media_extractor, duplicate_detector)
        
        # Test with published_parsed
        entry = MagicMock()
        entry.published_parsed = (2023, 12, 1, 10, 30, 0, 0, 0)
        result = fetcher._extract_entry_published(entry)
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 1
        assert result.hour == 10
        assert result.minute == 30
        
        # Test with updated_parsed
        delattr(entry, 'published_parsed')
        entry.updated_parsed = (2023, 11, 15, 14, 20, 0, 0, 0)
        result = fetcher._extract_entry_published(entry)
        assert result.year == 2023
        assert result.month == 11
        assert result.day == 15
        
        # Test with invalid parsed data
        entry.updated_parsed = None
        entry.created_parsed = (2023, 10, 10)  # Invalid tuple length
        result = fetcher._extract_entry_published(entry)
        # Should return current time
        assert result.tzinfo == timezone.utc
        
        # Test with no date fields
        delattr(entry, 'created_parsed')
        result = fetcher._extract_entry_published(entry)
        assert result.tzinfo == timezone.utc