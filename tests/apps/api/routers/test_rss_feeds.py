import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from apps.api.routers.rss_feeds import (
    create_user_rss_feed, get_user_rss_feeds, get_user_rss_feed,
    update_user_rss_feed, delete_user_rss_feed
)
from apps.api.models import UserRSSFeedCreate, UserRSSFeedUpdate
from apps.api.deps import get_current_user


@pytest.fixture
def mock_current_user():
    return {
        "id": 1,
        "email": "test@example.com",
        "language": "en",
        "is_active": True,
        "is_verified": True,
        "is_deleted": False,
        "created_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_rss_feed_repo():
    return AsyncMock()


@pytest.fixture
def client(mock_current_user):
    from fastapi import FastAPI
    from apps.api.routers.rss_feeds import router
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    return TestClient(app)


class TestRSSFeedsRouter:
    @pytest.mark.asyncio
    async def test_create_user_rss_feed_success(self, mock_current_user, mock_rss_feed_repo):
        """Test successful RSS feed creation"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo), \
             patch('apps.api.routers.rss_feeds.validate_rss_url', return_value=True):

            mock_rss_feed_repo.create_user_rss_feed.return_value = {
                "id": "feed_123",
                "user_id": 1,
                "url": "http://example.com/rss",
                "name": "Test Feed",
                "category_id": 1,
                "language": "en",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z"
            }

            feed_data = UserRSSFeedCreate(
                url="http://example.com/rss",
                name="Test Feed",
                category_id=1,
                language="en"
            )

            request = Request(scope={"type": "http", "method": "POST", "path": "/"})
            result = await create_user_rss_feed(request, feed_data, mock_current_user)

            assert result.id == "feed_123"
            assert result.url == "http://example.com/rss"
            mock_rss_feed_repo.create_user_rss_feed.assert_called_once_with(
                1, "http://example.com/rss", "Test Feed", 1, "en"
            )

    @pytest.mark.asyncio
    async def test_create_user_rss_feed_invalid_url(self, mock_current_user):
        """Test RSS feed creation with invalid URL"""
        with patch('apps.api.routers.rss_feeds.validate_rss_url', return_value=False):

            feed_data = UserRSSFeedCreate(url="invalid-url", name="Test Feed")
            request = Request(scope={"type": "http", "method": "POST", "path": "/"})

            with pytest.raises(HTTPException) as exc_info:
                await create_user_rss_feed(request, feed_data, mock_current_user)

            assert exc_info.value.status_code == 400
            assert "Invalid RSS URL format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_rss_feed_name_too_long(self, mock_current_user):
        """Test RSS feed creation with name too long"""
        with patch('apps.api.routers.rss_feeds.validate_rss_url', return_value=True):

            long_name = "A" * 256
            feed_data = UserRSSFeedCreate(url="http://example.com/rss", name=long_name)
            request = Request(scope={"type": "http", "method": "POST", "path": "/"})

            with pytest.raises(HTTPException) as exc_info:
                await create_user_rss_feed(request, feed_data, mock_current_user)

            assert exc_info.value.status_code == 400
            assert "Feed name too long" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_rss_feed_duplicate(self, mock_current_user, mock_rss_feed_repo):
        """Test RSS feed creation with duplicate URL"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo), \
             patch('apps.api.routers.rss_feeds.validate_rss_url', return_value=True):

            mock_rss_feed_repo.create_user_rss_feed.return_value = {"error": "duplicate"}

            feed_data = UserRSSFeedCreate(url="http://example.com/rss", name="Test Feed")
            request = Request(scope={"type": "http", "method": "POST", "path": "/"})

            with pytest.raises(HTTPException) as exc_info:
                await create_user_rss_feed(request, feed_data, mock_current_user)

            assert exc_info.value.status_code == 400
            assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_rss_feed_creation_failed(self, mock_current_user, mock_rss_feed_repo):
        """Test RSS feed creation when creation fails"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo), \
             patch('apps.api.routers.rss_feeds.validate_rss_url', return_value=True):

            mock_rss_feed_repo.create_user_rss_feed.return_value = None

            feed_data = UserRSSFeedCreate(url="http://example.com/rss", name="Test Feed")
            request = Request(scope={"type": "http", "method": "POST", "path": "/"})

            with pytest.raises(HTTPException) as exc_info:
                await create_user_rss_feed(request, feed_data, mock_current_user)

            assert exc_info.value.status_code == 500
            assert "Failed to create RSS feed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_user_rss_feeds_success(self, client, mock_rss_feed_repo):
        """Test successful retrieval of user RSS feeds"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.get_user_rss_feeds.return_value = [
                {
                    "id": "feed_1",
                    "user_id": 1,
                    "url": "http://example1.com/rss",
                    "name": "Feed 1",
                    "category_id": 1,
                    "language": "en",
                    "is_active": True,
                    "created_at": "2023-01-01T00:00:00Z"
                },
                {
                    "id": "feed_2",
                    "user_id": 1,
                    "url": "http://example2.com/rss",
                    "name": "Feed 2",
                    "category_id": 2,
                    "language": "ru",
                    "is_active": False,
                    "created_at": "2023-01-02T00:00:00Z"
                }
            ]

            response = client.get("/api/v1/users/me/rss-feeds")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            assert len(data["results"]) == 2
            assert data["results"][0]["name"] == "Feed 1"
            assert data["results"][1]["name"] == "Feed 2"
            mock_rss_feed_repo.get_user_rss_feeds.assert_called_once_with(1, 50, 0)

    @pytest.mark.asyncio
    async def test_get_user_rss_feeds_with_pagination(self, client, mock_rss_feed_repo):
        """Test user RSS feeds with custom pagination"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.get_user_rss_feeds.return_value = []

            response = client.get("/api/v1/users/me/rss-feeds?limit=10&offset=20")

            assert response.status_code == 200
            mock_rss_feed_repo.get_user_rss_feeds.assert_called_once_with(1, 10, 20)

    @pytest.mark.asyncio
    async def test_get_user_rss_feed_success(self, client, mock_rss_feed_repo):
        """Test successful retrieval of specific RSS feed"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.get_user_rss_feed_by_id.return_value = {
                "id": "feed_123",
                "user_id": 1,
                "url": "http://example.com/rss",
                "name": "Test Feed",
                "category_id": 1,
                "language": "en",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z"
            }

            response = client.get("/api/v1/users/me/rss-feeds/feed_123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "feed_123"
            assert data["name"] == "Test Feed"
            mock_rss_feed_repo.get_user_rss_feed_by_id.assert_called_once_with(1, "feed_123")

    @pytest.mark.asyncio
    async def test_get_user_rss_feed_not_found(self, client, mock_rss_feed_repo):
        """Test retrieval of non-existent RSS feed"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.get_user_rss_feed_by_id.return_value = None

            response = client.get("/api/v1/users/me/rss-feeds/feed_999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user_rss_feed_success(self, client, mock_rss_feed_repo):
        """Test successful RSS feed update"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.update_user_rss_feed.return_value = {
                "id": "feed_123",
                "user_id": 1,
                "url": "http://example.com/rss",
                "name": "Updated Feed",
                "category_id": 2,
                "language": "en",
                "is_active": False,
                "created_at": "2023-01-01T00:00:00Z"
            }

            update_data = UserRSSFeedUpdate(name="Updated Feed", category_id=2, is_active=False)

            response = client.put("/api/v1/users/me/rss-feeds/feed_123", json=update_data.model_dump())

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Feed"
            mock_rss_feed_repo.update_user_rss_feed.assert_called_once_with(
                1, "feed_123", {"name": "Updated Feed", "category_id": 2, "is_active": False}
            )

    @pytest.mark.asyncio
    async def test_update_user_rss_feed_name_too_long(self, client):
        """Test RSS feed update with name too long"""
        long_name = "A" * 256
        update_data = UserRSSFeedUpdate(name=long_name)

        response = client.put("/api/v1/users/me/rss-feeds/feed_123", json=update_data.model_dump())

        assert response.status_code == 400
        assert "Feed name too long" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user_rss_feed_partial_update(self, client, mock_rss_feed_repo):
        """Test partial RSS feed update"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.update_user_rss_feed.return_value = {
                "id": "feed_123",
                "user_id": 1,
                "url": "http://example.com/rss",
                "name": "Only Name Updated",
                "category_id": 1,
                "language": "en",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z"
            }

            update_data = UserRSSFeedUpdate(name="Only Name Updated")

            response = client.put("/api/v1/users/me/rss-feeds/feed_123", json=update_data.model_dump())

            assert response.status_code == 200
            mock_rss_feed_repo.update_user_rss_feed.assert_called_once_with(
                1, "feed_123", {"name": "Only Name Updated"}
            )

    @pytest.mark.asyncio
    async def test_update_user_rss_feed_not_found(self, client, mock_rss_feed_repo):
        """Test update of non-existent RSS feed"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.update_user_rss_feed.return_value = None

            update_data = UserRSSFeedUpdate(name="New Name")

            response = client.put("/api/v1/users/me/rss-feeds/feed_999", json=update_data.model_dump())

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_user_rss_feed_success(self, client, mock_rss_feed_repo):
        """Test successful RSS feed deletion"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.delete_user_rss_feed.return_value = True

            response = client.delete("/api/v1/users/me/rss-feeds/feed_123")

            assert response.status_code == 204
            mock_rss_feed_repo.delete_user_rss_feed.assert_called_once_with(1, "feed_123")

    @pytest.mark.asyncio
    async def test_delete_user_rss_feed_not_found(self, client, mock_rss_feed_repo):
        """Test deletion of non-existent RSS feed"""
        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.delete_user_rss_feed.return_value = False

            response = client.delete("/api/v1/users/me/rss-feeds/feed_999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    # Database error tests for all endpoints
    @pytest.mark.asyncio
    async def test_create_user_rss_feed_database_error(self, client, mock_rss_feed_repo):
        """Test create RSS feed with database error"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo), \
             patch('apps.api.routers.rss_feeds.validate_rss_url', return_value=True):

            mock_rss_feed_repo.create_user_rss_feed.side_effect = DatabaseException("DB error")

            feed_data = UserRSSFeedCreate(url="http://example.com/rss", name="Test Feed")

            response = client.post("/api/v1/users/me/rss-feeds", json=feed_data.model_dump())

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_rss_feeds_database_error(self, client, mock_rss_feed_repo):
        """Test get RSS feeds with database error"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.get_user_rss_feeds.side_effect = DatabaseException("DB error")

            response = client.get("/api/v1/users/me/rss-feeds")

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_rss_feed_database_error(self, client, mock_rss_feed_repo):
        """Test get specific RSS feed with database error"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.get_user_rss_feed_by_id.side_effect = DatabaseException("DB error")

            response = client.get("/api/v1/users/me/rss-feeds/feed_123")

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user_rss_feed_database_error(self, client, mock_rss_feed_repo):
        """Test update RSS feed with database error"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.update_user_rss_feed.side_effect = DatabaseException("DB error")

            update_data = UserRSSFeedUpdate(name="New Name")

            response = client.put("/api/v1/users/me/rss-feeds/feed_123", json=update_data.model_dump())

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_user_rss_feed_database_error(self, client, mock_rss_feed_repo):
        """Test delete RSS feed with database error"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.rss_feeds.get_service', return_value=mock_rss_feed_repo):

            mock_rss_feed_repo.delete_user_rss_feed.side_effect = DatabaseException("DB error")

            response = client.delete("/api/v1/users/me/rss-feeds/feed_123")

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]