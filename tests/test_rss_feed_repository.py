import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from repositories.rss_feed_repository import RSSFeedRepository
from exceptions import DatabaseException


@pytest.fixture
def repo(mock_db_pool):
    return RSSFeedRepository(mock_db_pool)


class TestRSSFeedRepository:
    @pytest.mark.asyncio
    async def test_create_user_rss_feed_success(self, repo, mock_db_pool):
        """Test successful creation of user RSS feed"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        # Mock duplicate check - no existing feed
        cur.fetchone.side_effect = [None, ("feed_123", "http://example.com/rss", "Test Feed", 1, "en", True, "2023-01-01", "2023-01-01")]

        result = await repo.create_user_rss_feed(1, "http://example.com/rss", "Test Feed", 1, "en")

        assert result == {
            "id": "feed_123", "url": "http://example.com/rss", "name": "Test Feed",
            "category_id": 1, "language": "en", "is_active": True,
            "created_at": "2023-01-01", "updated_at": "2023-01-01"
        }
        cur.execute.assert_called()

    @pytest.mark.asyncio
    async def test_create_user_rss_feed_duplicate(self, repo, mock_db_pool):
        """Test creation when feed already exists"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        # Mock duplicate check - existing feed found
        cur.fetchone.return_value = ("existing_id",)

        result = await repo.create_user_rss_feed(1, "http://example.com/rss", "Test Feed", 1, "en")

        assert result == {"error": "duplicate"}

    @pytest.mark.asyncio
    async def test_create_user_rss_feed_database_error(self, repo, mock_db_pool):
        """Test creation with database error"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.side_effect = Exception("DB error")

        with pytest.raises(DatabaseException):
            await repo.create_user_rss_feed(1, "http://example.com/rss", "Test Feed", 1, "en")

    @pytest.mark.asyncio
    async def test_get_user_rss_feeds_success(self, repo, mock_db_pool):
        """Test successful retrieval of user RSS feeds"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()

        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[
            ("feed_1", "http://example1.com", "Feed 1", 1, "en", True, "2023-01-01", "2023-01-01"),
            ("feed_2", "http://example2.com", "Feed 2", 2, "ru", False, "2023-01-02", "2023-01-02")
        ])

        result = await repo.get_user_rss_feeds(1, 10, 0)

        assert len(result) == 2
        assert result[0]["id"] == "feed_1"
        assert result[1]["name"] == "Feed 2"

    @pytest.mark.asyncio
    async def test_get_user_rss_feeds_database_error(self, repo, mock_db_pool):
        """Test get user RSS feeds with database error"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.execute = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(DatabaseException):
            await repo.get_user_rss_feeds(1, 10, 0)

    @pytest.mark.asyncio
    async def test_get_user_rss_feed_by_id_success(self, repo, mock_db_pool, mock_cursor):
        """Test successful retrieval of specific user RSS feed"""
        # Setup cursor to return test data
        mock_cursor.fetchone.return_value = ("feed_123", "http://example.com/rss", "Test Feed", 1, "en", True, "2023-01-01", "2023-01-01")
        
        # Use the mock cursor directly
        conn = mock_db_pool.acquire.return_value.return_value
        conn.cursor_mock = mock_cursor

        result = await repo.get_user_rss_feed_by_id(1, "feed_123")

        assert result["id"] == "feed_123"
        assert result["name"] == "Test Feed"

    @pytest.mark.asyncio
    async def test_get_user_rss_feed_by_id_not_found(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test retrieval of non-existent user RSS feed"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        cur.fetchone.return_value = None

        result = await repo.get_user_rss_feed_by_id(1, "feed_999")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_rss_feed_success(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test successful update of user RSS feed"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        cur.fetchone.return_value = ("feed_123", "http://example.com/rss", "Updated Feed", 2, "en", False, "2023-01-01", "2023-01-02")

        update_data = {"name": "Updated Feed", "category_id": 2, "is_active": False}
        result = await repo.update_user_rss_feed(1, "feed_123", update_data)

        assert result["name"] == "Updated Feed"
        assert result["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_user_rss_feed_not_found(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test update of non-existent user RSS feed"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        cur.fetchone.return_value = None

        update_data = {"name": "New Name"}
        result = await repo.update_user_rss_feed(1, "feed_999", update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_rss_feed_success(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test successful deletion of user RSS feed"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        cur.rowcount = 1

        result = await repo.delete_user_rss_feed(1, "feed_123")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_user_rss_feed_not_found(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test deletion of non-existent user RSS feed"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        cur.rowcount = 0

        result = await repo.delete_user_rss_feed(1, "feed_999")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_active_feeds_success(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test successful retrieval of all active feeds"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[
            (1, "http://feed1.com", "Feed 1", "en", 1, 1, "Source 1", "Tech"),
            (2, "http://feed2.com", "Feed 2", "ru", 2, 2, "Source 2", "News")
        ])

        result = await repo.get_all_active_feeds()

        assert len(result) == 2
        assert result[0]["name"] == "Feed 1"
        assert result[1]["category"] == "News"

    @pytest.mark.asyncio
    async def test_get_feeds_by_category_success(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test successful retrieval of feeds by category"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[
            (1, "http://feed1.com", "Feed 1", "en", 1, 1, "Source 1", "Tech")
        ])

        result = await repo.get_feeds_by_category("Tech")

        assert len(result) == 1
        assert result[0]["category"] == "Tech"

    @pytest.mark.asyncio
    async def test_get_feeds_by_language_success(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test successful retrieval of feeds by language"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[
            (1, "http://feed1.com", "Feed 1", "en", 1, 1, "Source 1", "Tech")
        ])

        result = await repo.get_feeds_by_language("en")

        assert len(result) == 1
        assert result[0]["lang"] == "en"

    @pytest.mark.asyncio
    async def test_get_feeds_by_source_success(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test successful retrieval of feeds by source"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        # Mock the execute method
        cur.execute = AsyncMock()
        
        # Mock fetchall to return test data
        cur.fetchall = AsyncMock(return_value=[
            (1, "http://feed1.com", "Feed 1", "en", 1, 1, "BBC", "News")
        ])

        result = await repo.get_feeds_by_source("BBC")

        assert len(result) == 1
        assert result[0]["source"] == "BBC"

    # Database error tests for all methods
    @pytest.mark.asyncio
    async def test_get_all_active_feeds_database_error(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test get_all_active_feeds with database error"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.execute = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(DatabaseException):
            await repo.get_all_active_feeds()

    @pytest.mark.asyncio
    async def test_get_feeds_by_category_database_error(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test get_feeds_by_category with database error"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.execute = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(DatabaseException):
            await repo.get_feeds_by_category("Tech")

    @pytest.mark.asyncio
    async def test_get_feeds_by_language_database_error(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test get_feeds_by_language with database error"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.execute = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(DatabaseException):
            await repo.get_feeds_by_language("en")

    @pytest.mark.asyncio
    async def test_get_feeds_by_source_database_error(self, repo, mock_db_pool, mock_conn, mock_cur):
        """Test get_feeds_by_source with database error"""
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.execute = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(DatabaseException):
            await repo.get_feeds_by_source("BBC")