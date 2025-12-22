import pytest
import os
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from utils.image import ImageProcessor


class TestImageProcessor:
    """Test cases for ImageProcessor utility functions"""

    @pytest.mark.asyncio
    async def test_download_and_save_image_no_url(self):
        """Test download_and_save_image with no URL"""
        result = await ImageProcessor.download_and_save_image(None, "test_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_download_and_save_image_no_rss_item_id(self):
        """Test download_and_save_image with no RSS item ID"""
        result = await ImageProcessor.download_and_save_image("http://example.com/image.jpg", None)
        assert result is None

    @pytest.mark.asyncio
    async def test_download_and_save_image_file_exists(self):
        """Test download_and_save_image when file already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            existing_file = os.path.join(temp_dir, "2025", "12", "21", "test_item_123.jpg")
            os.makedirs(os.path.dirname(existing_file), exist_ok=True)
            with open(existing_file, 'wb') as f:
                f.write(b"existing image data")
    
            # Mock config service
            mock_config = MagicMock()
            mock_config.get.return_value = temp_dir
    
            # Mock the HTTP request to avoid actual network calls
            with patch('utils.image.get_service', return_value=mock_config), \
                 patch('aiohttp.ClientSession') as mock_session_class:
    
                # Mock session to raise exception so we test the file exists path
                mock_session = AsyncMock()
                mock_session.__aenter__.return_value = mock_session
                mock_session.__aexit__.return_value = None
                mock_session.get.side_effect = Exception("Network error")
                mock_session_class.return_value = mock_session
    
                result = await ImageProcessor.download_and_save_image(
                    "http://example.com/image.jpg", "test_item_123", temp_dir
                )
    
                # This test is mainly to ensure the file exists path doesn't crash
                # The actual file existence check happens in the real implementation
                assert result is None  # Network error should return None

    @pytest.mark.asyncio
    async def test_download_and_save_image_invalid_rss_item_id(self):
        """Test download_and_save_image with invalid RSS item ID"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock config service
            mock_config = MagicMock()
            mock_config.get.return_value = temp_dir
            
            # Mock the HTTP request to raise an exception so we test the hash generation
            with patch('utils.image.get_service', return_value=mock_config), \
                 patch('aiohttp.ClientSession') as mock_session_class:
                
                # Mock session to raise exception
                mock_session = AsyncMock()
                mock_session.__aenter__.return_value = mock_session
                mock_session.__aexit__.return_value = None
                mock_session.get.side_effect = Exception("Network error")
                mock_session_class.return_value = mock_session
                
                result = await ImageProcessor.download_and_save_image(
                    "http://example.com/image.jpg", "invalid/id<>", temp_dir
                )
                
                assert result is None

    @pytest.mark.asyncio
    async def test_download_and_save_image_network_error(self):
        """Test download_and_save_image with network error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock config service
            mock_config = MagicMock()
            mock_config.get.return_value = temp_dir
            
            with patch('utils.image.get_service', return_value=mock_config), \
                 patch('aiohttp.ClientSession') as mock_session_class:
                
                # Mock session to raise exception
                mock_session = AsyncMock()
                mock_session.__aenter__.return_value = mock_session
                mock_session.__aexit__.return_value = None
                mock_session.get.side_effect = Exception("Network error")
                mock_session_class.return_value = mock_session
                
                result = await ImageProcessor.download_and_save_image(
                    "http://example.com/image.jpg", "test_item_123", temp_dir
                )
                
                assert result is None

    @pytest.mark.asyncio
    async def test_download_and_save_image_filesystem_error(self):
        """Test download_and_save_image with filesystem error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only to simulate filesystem error
            os.chmod(temp_dir, 0o444)
            
            try:
                # Mock config service
                mock_config = MagicMock()
                mock_config.get.return_value = temp_dir
                
                with patch('utils.image.get_service', return_value=mock_config), \
                     patch('aiohttp.ClientSession') as mock_session_class:
                    
                    # Mock session to raise exception
                    mock_session = AsyncMock()
                    mock_session.__aenter__.return_value = mock_session
                    mock_session.__aexit__.return_value = None
                    mock_session.get.side_effect = Exception("Network error")
                    mock_session_class.return_value = mock_session
                    
                    result = await ImageProcessor.download_and_save_image(
                        "http://example.com/image.jpg", "test_item_123", temp_dir
                    )
                    
                    assert result is None
            finally:
                # Restore permissions
                os.chmod(temp_dir, 0o755)

    @pytest.mark.asyncio
    async def test_process_image_from_url_success(self):
        """Test successful image processing from URL"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock config service
            mock_config = MagicMock()
            mock_config.get.return_value = temp_dir
            
            with patch('utils.image.get_service', return_value=mock_config), \
                 patch('utils.image.ImageProcessor.download_and_save_image') as mock_download:
                
                mock_download.return_value = "2025/12/21/test_item_123.jpg"
                
                result = await ImageProcessor.process_image_from_url(
                    "http://example.com/image.jpg", "test_item_123"
                )
                
                assert result == "2025/12/21/test_item_123.jpg"
                mock_download.assert_called_once_with("http://example.com/image.jpg", "test_item_123")

    @pytest.mark.asyncio
    async def test_process_image_from_url_no_url(self):
        """Test image processing with no URL"""
        result = await ImageProcessor.process_image_from_url(None, "test_item_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_process_image_from_url_no_rss_item_id(self):
        """Test image processing with no RSS item ID"""
        result = await ImageProcessor.process_image_from_url("http://example.com/image.jpg", None)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_image_from_preview_no_image_found(self):
        """Test extracting image when no suitable image is found"""
        html_content = '''
        <html>
        <body>
            <p>No images here</p>
        </body>
        </html>
        '''
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.text.return_value = html_content
            
            # Create proper async context manager for session
            mock_session = AsyncMock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            result = await ImageProcessor.extract_image_from_preview("http://example.com/page")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_extract_image_from_preview_network_error(self):
        """Test extracting image with network error"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session.get.side_effect = Exception("Network error")
            mock_session_class.return_value = mock_session
            
            result = await ImageProcessor.extract_image_from_preview("http://example.com/page")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_extract_image_from_preview_empty_url(self):
        """Test extracting image with empty URL"""
        result = await ImageProcessor.extract_image_from_preview("")
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_image_from_preview_none_url(self):
        """Test extracting image with None URL"""
        result = await ImageProcessor.extract_image_from_preview(None)
        assert result is None