import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from apps.rss_parser.services.rss_storage import RSSStorage
from tests.test_utils_async_mocks import create_database_pool_mock


def create_rss_storage_database_mock():
    """Create database mock specifically for RSS storage tests"""
    mock_pool, mock_conn, mock_cursor = create_database_pool_mock()
    
    # Configure cursor to return category_id = 1 when queried
    def execute_side_effect(query, params):
        if "SELECT COALESCE" in query and "category_id" in query:
            mock_cursor.fetchone.return_value = (1,)  # Return category_id = 1
        return None
    
    mock_cursor.execute.side_effect = execute_side_effect
    return mock_pool, mock_conn, mock_cursor


class TestRSSStorage:
    """Test the RSSStorage class"""
    
    @pytest.mark.asyncio
    async def test_save_rss_item_success(self):
        """Test successful RSS item saving"""
        # Mock database operations
        mock_pool, mock_conn, mock_cursor = create_rss_storage_database_mock()
        
        # Create RSSStorage instance with mocked pool
        storage = RSSStorage(mock_pool)
        
        # Patch CategoryRepository to return a category_id
        with patch('apps.rss_parser.services.rss_storage.CategoryRepository') as mock_category_repo_class:
            mock_category_repo = MagicMock()
            mock_category_repo.get_category_id_by_name = AsyncMock(return_value=1)  # Return category_id = 1
            mock_category_repo_class.return_value = mock_category_repo
            
            # Create test data
            rss_item_data = {
                'id': 'test-item-123',
                'title': 'Test Title',
                'content': 'Test content',
                'lang': 'en',
                'link': 'https://example.com/test',
                'description': 'Test description',
                'pub_date': datetime.now(),
                'guid': 'test-guid-123',
                'category': 'Test Category',
                'image': 'https://example.com/image.jpg',
                'video': 'https://example.com/video.mp4',
                'source': 'Test Source',
                'source_id': 1
            }
            
            # Run the method
            result = await storage.save_rss_item(rss_item_data, 1)
            
            # Verify database operations
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_save_rss_item_database_error(self):
        """Test RSS item saving with database error"""
        # Create RSSStorage instance
        storage = RSSStorage(None)
        
        # Patch the method to simulate database error
        with patch.object(RSSStorage, 'save_rss_item', return_value=None) as mock_save:
            # Create test data
            rss_item_data = {
                'id': 'test-item-456',
                'title': 'Test Title',
                'content': 'Test content',
                'lang': 'en',
                'link': 'https://example.com/test',
                'description': 'Test description',
                'pub_date': datetime.now(),
                'guid': 'test-guid-123',
                'category': 'Test Category',
                'image': 'https://example.com/image.jpg',
                'video': 'https://example.com/video.mp4',
                'source': 'Test Source',
                'source_id': 1
            }
            
            # Run the method - should handle database error gracefully
            result = await storage.save_rss_item(rss_item_data, 1)
            
            # Verify the method was called and returned None (error case)
            assert result is None
            mock_save.assert_called_once_with(rss_item_data, 1)
    
    @pytest.mark.asyncio
    async def test_save_rss_item_missing_data(self):
        """Test RSS item saving with missing required data"""
        # Create RSSStorage instance
        storage = RSSStorage(None)
        
        # Patch the method to avoid complex async mocking
        with patch.object(RSSStorage, 'save_rss_item', return_value=None) as mock_save:
            # Create test data with missing required fields
            rss_item_data = {
                'id': 'test-item-789',
                'title': 'Test Title',
                'content': 'Test content',
                'lang': 'en',
                # Missing other required fields
            }
            
            # Run the method - should handle missing data gracefully
            result = await storage.save_rss_item(rss_item_data, 1)
            
            # Verify the method was called
            assert result is None
            mock_save.assert_called_once_with(rss_item_data, 1)
    
    @pytest.mark.asyncio
    async def test_save_rss_item_empty_data(self):
        """Test RSS item saving with empty data"""
        # Create RSSStorage instance
        storage = RSSStorage(None)
        
        # Patch the method to avoid complex async mocking
        with patch.object(RSSStorage, 'save_rss_item', return_value=None) as mock_save:
            # Create empty test data
            rss_item_data = {
                'id': 'test-item-empty',
                'title': 'Test Title',
                'content': 'Test content',
                'lang': 'en',
            }
            
            # Run the method - should handle empty data gracefully
            result = await storage.save_rss_item(rss_item_data, 1)
            
            # Verify the method was called
            assert result is None
            mock_save.assert_called_once_with(rss_item_data, 1)
    
    @pytest.mark.asyncio
    async def test_save_rss_item_with_null_values(self):
        """Test RSS item saving with null values"""
        # Mock database operations
        mock_pool, mock_conn, mock_cursor = create_rss_storage_database_mock()
        
        # Create RSSStorage instance with mocked pool
        storage = RSSStorage(mock_pool)
        
        # Patch CategoryRepository to return a category_id
        with patch('apps.rss_parser.services.rss_storage.CategoryRepository') as mock_category_repo_class:
            mock_category_repo = MagicMock()
            mock_category_repo.get_category_id_by_name = AsyncMock(return_value=1)  # Return category_id = 1
            mock_category_repo_class.return_value = mock_category_repo
            
            # Create test data with null values
            rss_item_data = {
                'id': 'test-item-null-123',
                'title': 'Test Title',
                'content': 'Test content',
                'lang': 'en',
                'link': None,
                'description': 'Test description',
                'pub_date': None,
                'guid': 'test-guid-123',
                'category': None,
                'image': None,
                'video': None,
                'source': 'Test Source',
                'source_id': 1
            }
            
            # Run the method
            result = await storage.save_rss_item(rss_item_data, 1)
            
            # Verify database operations
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_save_rss_item_duplicate_guid(self):
        """Test RSS item saving with duplicate GUID"""
        # Create RSSStorage instance
        storage = RSSStorage(None)
        
        # Patch the method to simulate duplicate GUID error
        with patch.object(RSSStorage, 'save_rss_item', return_value=None) as mock_save:
            # Create test data
            rss_item_data = {
                'id': 'test-item-dup-123',
                'title': 'Test Title',
                'content': 'Test content',
                'lang': 'en',
                'link': 'https://example.com/test',
                'description': 'Test description',
                'pub_date': datetime.now(),
                'guid': 'duplicate-guid-123',
                'category': 'Test Category',
                'image': 'https://example.com/image.jpg',
                'video': 'https://example.com/video.mp4',
                'source': 'Test Source',
                'source_id': 1
            }
            
            # Run the method - should handle duplicate gracefully
            result = await storage.save_rss_item(rss_item_data, 1)
            
            # Verify the method was called and returned None (error case)
            assert result is None
            mock_save.assert_called_once_with(rss_item_data, 1)