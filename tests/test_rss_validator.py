import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from apps.rss_parser.services.rss_validator import RSSValidator


class TestRSSValidator:
    """Test the RSSValidator class"""
    
    def test_init(self):
        """Test RSSValidator initialization"""
        validator = RSSValidator(cache_ttl=600, request_timeout=15)
        
        assert validator._validation_cache == {}
        assert validator._cache_ttl == 600
        assert validator._request_timeout == 15
    
    def test_init_default_params(self):
        """Test RSSValidator initialization with default parameters"""
        validator = RSSValidator()
        
        assert validator._cache_ttl == 300
        assert validator._request_timeout == 10
    
    @pytest.mark.asyncio
    async def test_validate_feed_cache_hit(self):
        """Test validation with cache hit"""
        validator = RSSValidator(cache_ttl=300)
        
        # Pre-populate cache
        validator._validation_cache["https://example.com/feed"] = (True, time.time())
        
        result = await validator.validate_feed("https://example.com/feed", {})
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_feed_cache_expired(self):
        """Test validation with expired cache"""
        validator = RSSValidator(cache_ttl=1)  # 1 second TTL
        
        # Pre-populate cache with old timestamp
        old_time = time.time() - 2  # 2 seconds ago
        validator._validation_cache["https://example.com/feed"] = (True, old_time)
        
        # Mock the validation to fail and check that cache is updated
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Mock session to raise exception
            mock_session_class.side_effect = Exception("Network error")
            
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is False
            # Cache should be updated with new (invalid) result
            assert validator._validation_cache["https://example.com/feed"][0] is False
    
    @pytest.mark.asyncio
    async def test_validate_feed_network_error(self):
        """Test validation with network error"""
        validator = RSSValidator()
        
        # Mock aiohttp to raise exception
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.side_effect = Exception("Network error")
            
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is False
            # Should be cached as invalid
            assert validator._validation_cache["https://example.com/feed"][0] is False
    
    @pytest.mark.asyncio
    async def test_validate_feed_bozo_non_encoding_error(self):
        """Test validation with bozo exception for non-encoding error"""
        validator = RSSValidator()
        
        # Mock feedparser to return bozo feed with non-encoding error
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("Some other parsing error")
        mock_feed.entries = [1, 2, 3]
        
        with patch('feedparser.parse', return_value=mock_feed):
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is False  # Should be invalid due to bozo exception
    
    @pytest.mark.asyncio
    async def test_validate_feed_no_entries(self):
        """Test validation with no entries"""
        validator = RSSValidator()
        
        # Mock feedparser to return feed with no entries
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = []
        
        with patch('feedparser.parse', return_value=mock_feed):
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is False  # Should be invalid due to no entries
    
    @pytest.mark.asyncio
    async def test_validate_feed_no_entries_attribute(self):
        """Test validation with no entries attribute"""
        validator = RSSValidator()
        
        # Mock feedparser to return feed with no entries attribute
        mock_feed = MagicMock()
        mock_feed.bozo = False
        del mock_feed.entries
        
        with patch('feedparser.parse', return_value=mock_feed):
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is False  # Should be invalid due to no entries
    
    @pytest.mark.asyncio
    async def test_validate_feed_raw_content_fallback_failure(self):
        """Test validation with raw content fallback failure"""
        validator = RSSValidator()
        
        # Mock feedparser to fail on URL parsing with the specific error, then fail again
        first_parse = MagicMock()
        first_parse.bozo = False
        first_parse.entries = []
        
        # Create a specific exception for the first parse
        parse_exception = Exception("expected string or bytes-like object, got 'dict'")
        
        # Mock raw content parsing to raise exception
        with patch('feedparser.parse') as mock_parse:
            mock_parse.side_effect = [parse_exception, Exception("Raw content parsing error")]
            
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is False  # Should be invalid due to raw content parsing failure
    
    @pytest.mark.asyncio
    async def test_validate_feed_successful_validation(self):
        """Test successful validation"""
        validator = RSSValidator()
        
        # Mock feedparser to return valid feed
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [1, 2, 3]
        
        with patch('feedparser.parse', return_value=mock_feed):
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is True  # Should be valid
            assert validator._validation_cache["https://example.com/feed"][0] is True
    
    @pytest.mark.asyncio
    async def test_validate_feed_bozo_encoding_error(self):
        """Test validation with bozo exception for encoding (should be ignored)"""
        validator = RSSValidator()
        
        # Mock feedparser with encoding bozo exception
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("document declared as us-ascii, but parsed as utf-8")
        mock_feed.entries = [1, 2, 3]
        
        with patch('feedparser.parse', return_value=mock_feed):
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is True  # Should be valid despite bozo exception
            assert validator._validation_cache["https://example.com/feed"][0] is True
    
    @pytest.mark.asyncio
    async def test_validate_feed_raw_content_fallback_success(self):
        """Test validation with raw content fallback success"""
        validator = RSSValidator()
        
        # Mock feedparser to fail on URL parsing with the specific error, then succeed
        first_parse = MagicMock()
        first_parse.bozo = False
        first_parse.entries = []
        
        second_parse = MagicMock()
        second_parse.bozo = False
        second_parse.entries = [1, 2, 3]
        
        # Create a specific exception for the first parse
        parse_exception = Exception("expected string or bytes-like object, got 'dict'")
        
        with patch('feedparser.parse') as mock_parse:
            # First call raises the specific exception, second call succeeds
            mock_parse.side_effect = [parse_exception, second_parse]
            
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is True  # Should be valid due to successful raw content parsing
            assert validator._validation_cache["https://example.com/feed"][0] is True
    
    @pytest.mark.asyncio
    async def test_validate_feed_raw_content_fallback_encoding_error(self):
        """Test validation with raw content fallback encoding error"""
        validator = RSSValidator()
        
        # Mock feedparser to fail on URL parsing
        first_parse = MagicMock()
        first_parse.bozo = False
        first_parse.entries = []
        
        # Create a specific exception for the first parse
        parse_exception = Exception("expected string or bytes-like object, got 'dict'")
        
        # Mock raw content parsing with encoding error
        second_parse = MagicMock()
        second_parse.bozo = True
        second_parse.bozo_exception = Exception("document declared as us-ascii, but parsed as utf-8")
        second_parse.entries = [1, 2, 3]
        
        with patch('feedparser.parse') as mock_parse:
            mock_parse.side_effect = [parse_exception, second_parse]
            
            result = await validator.validate_feed("https://example.com/feed", {})
            
            assert result is True  # Should be valid despite encoding error in raw content
            assert validator._validation_cache["https://example.com/feed"][0] is True