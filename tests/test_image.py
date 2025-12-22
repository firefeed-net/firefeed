import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp
from utils.image import ImageProcessor


class TestImageProcessor:
    @pytest.mark.asyncio
    async def test_download_and_save_image_no_url(self):
        """Test download_and_save_image with no URL"""
        result = await ImageProcessor.download_and_save_image(None, "123")
        assert result is None

    @pytest.mark.asyncio
    async def test_download_and_save_image_no_rss_item_id(self):
        """Test download_and_save_image with no rss_item_id"""
        result = await ImageProcessor.download_and_save_image("http://example.com/image.jpg", None)
        assert result is None

    @pytest.mark.asyncio
    async def test_download_and_save_image_success(self):
        """Test successful image download and save"""
        with patch('utils.image.get_service') as mock_get_service, \
             patch('utils.image.aiohttp.ClientSession') as mock_session_class, \
             patch('utils.image.aiofiles.open', create=True) as mock_aiofiles_open, \
             patch('utils.image.os.makedirs') as mock_makedirs, \
             patch('utils.image.os.path.exists', return_value=False), \
             patch('utils.image.os.path.relpath', return_value="2023/12/20/123.jpg") as mock_relpath:

            # Mock config
            mock_config = {'IMAGES_ROOT_DIR': '/tmp/images', 'IMAGE_FILE_EXTENSIONS': ['.jpg', '.png']}
            mock_get_service.return_value = mock_config

            # Mock response
            mock_response = AsyncMock()
            mock_response.headers = {'Content-Type': 'image/jpeg'}
            mock_response.read.return_value = b'fake image data'
            mock_response.raise_for_status.return_value = None

            # Create a proper async context manager for the response
            class MockAsyncContextManager:
                def __init__(self, response):
                    self.response = response
                
                async def __aenter__(self):
                    return self.response
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            # Create a proper async context manager for the session
            class MockSessionContextManager:
                def __init__(self, response):
                    self.response = response
                
                async def __aenter__(self):
                    session = AsyncMock()
                    session.get = lambda url, headers=None: MockAsyncContextManager(self.response)
                    return session
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            # Mock aiofiles
            class MockFileContextManager:
                def __init__(self):
                    self.file = AsyncMock()
                
                async def __aenter__(self):
                    return self.file
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_session_class.return_value = MockSessionContextManager(mock_response)
            mock_aiofiles_open.return_value = MockFileContextManager()

            result = await ImageProcessor.download_and_save_image("http://example.com/image.jpg", "123")

            assert result == "2023/12/20/123.jpg"
            mock_makedirs.assert_called_once()
            mock_file = mock_aiofiles_open.return_value.file
            mock_file.write.assert_called_once_with(b'fake image data')

    @pytest.mark.asyncio
    async def test_download_and_save_image_file_exists(self):
        """Test download when file already exists"""
        with patch('utils.image.get_service') as mock_get_service, \
             patch('utils.image.datetime') as mock_datetime:

            mock_config = {'IMAGES_ROOT_DIR': '/tmp/images', 'IMAGE_FILE_EXTENSIONS': ['.jpg', '.png']}
            mock_get_service.return_value = mock_config

            # Mock datetime.now() to return an object with strftime method
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2023/12/20"
            mock_datetime.now.return_value = mock_now

            with patch('utils.image.os.makedirs') as mock_makedirs, \
                 patch('utils.image.os.path.exists') as mock_exists, \
                 patch('utils.image.os.path.relpath', return_value="2023/12/20/123.jpg") as mock_relpath, \
                 patch('utils.image.aiohttp.ClientSession') as mock_session_class, \
                 patch('utils.image.aiofiles.open', create=True) as mock_aiofiles_open:

                # Create proper async context manager for the response
                class MockAsyncContextManager:
                    def __init__(self, response):
                        self.response = response
                    
                    async def __aenter__(self):
                        return self.response
                    
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        return None

                # Create proper async context manager for the session
                class MockSessionContextManager:
                    def __init__(self, response):
                        self.response = response
                    
                    async def __aenter__(self):
                        session = AsyncMock()
                        session.get = lambda url, headers=None: MockAsyncContextManager(self.response)
                        return session
                    
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        return None

                # Create proper async context manager for aiofiles
                class MockFileContextManager:
                    def __init__(self):
                        self.file = AsyncMock()
                    
                    async def __aenter__(self):
                        return self.file
                    
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        return None

                # Mock response
                mock_response = AsyncMock()
                mock_response.headers = {'Content-Type': 'image/jpeg'}
                mock_response.read.return_value = b'fake image data'
                mock_response.raise_for_status.return_value = None

                # Make os.path.exists return True for the specific file path AFTER calculating file_path
                def exists_side_effect(path):
                    if "123.jpg" in str(path):
                        return True
                    return False
                mock_exists.side_effect = exists_side_effect

                mock_session_class.return_value = MockSessionContextManager(mock_response)
                mock_aiofiles_open.return_value = MockFileContextManager()
                
                result = await ImageProcessor.download_and_save_image("http://example.com/image.jpg", "123")

                assert result == "2023/12/20/123.jpg"

    @pytest.mark.asyncio
    async def test_process_image_from_url(self):
        """Test process_image_from_url"""
        with patch.object(ImageProcessor, 'download_and_save_image', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = "/path/to/image.jpg"

            result = await ImageProcessor.process_image_from_url("http://example.com/image.jpg", "123")

            assert result == "/path/to/image.jpg"
            mock_download.assert_called_once_with("http://example.com/image.jpg", "123")

    @pytest.mark.asyncio
    async def test_extract_image_from_preview_og_image(self):
        """Test extract_image_from_preview with og:image"""
        with patch('utils.image.aiohttp.ClientSession') as mock_session_class, \
             patch('utils.image.BeautifulSoup') as mock_bs, \
             patch('asyncio.get_event_loop') as mock_loop:

            # Create proper async context manager for response
            class MockAsyncContextManager:
                def __init__(self, response):
                    self.response = response
                
                async def __aenter__(self):
                    return self.response
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            # Create proper async context manager for session
            class MockSessionContextManager:
                def __init__(self, response):
                    self.response = response
                
                async def __aenter__(self):
                    session = MagicMock()
                    session.get = lambda url, headers=None: MockAsyncContextManager(self.response)
                    return session
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            # Mock the text method to return a coroutine
            async def mock_text():
                return "<html><head><meta property='og:image' content='http://example.com/og.jpg'></head></html>"
            
            mock_response = MagicMock()
            # Make raise_for_status not raise an exception (returns None)
            mock_response.raise_for_status = MagicMock(return_value=None)
            mock_response.text = mock_text
            mock_session_class.return_value = MockSessionContextManager(mock_response)

            # Create proper mock for the meta tag that supports both .get() and [] access
            class MockMetaTag:
                def __init__(self):
                    self.content = "http://example.com/og.jpg"
                
                def get(self, key):
                    if key == "content":
                        return self.content
                    return None
                
                def __getitem__(self, key):
                    if key == "content":
                        return self.content
                    raise KeyError(key)
            
            mock_meta = MockMetaTag()
            
            # Create proper mock for BeautifulSoup object
            mock_soup = MagicMock()
            mock_soup.find = MagicMock(return_value=mock_meta)
            mock_bs.return_value = mock_soup

            # Mock the executor call for BeautifulSoup to return a coroutine that yields the soup
            async def mock_run_in_executor(executor, func, *args):
                return mock_soup
            
            mock_loop.return_value.run_in_executor.side_effect = mock_run_in_executor

            result = await ImageProcessor.extract_image_from_preview("http://example.com")

            assert result == "http://example.com/og.jpg"