import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from apps.api.routers.users import router
from apps.api.models import UserUpdate
from apps.api.deps import get_current_user
from di_container import get_service


@pytest.fixture
def client(mock_current_user):
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    return TestClient(app)


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_rss_item_repo():
    return AsyncMock()


@pytest.fixture
def mock_current_user():
    return {
        "id": 1,
        "email": "test@example.com",
        "language": "en",
        "is_active": True,
        "is_verified": True,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc)
    }


class TestUsersRouter:
    @pytest.mark.asyncio
    async def test_get_current_user_profile_success(self, client, mock_current_user):
        """Test successful get current user profile"""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["language"] == "en"

    @pytest.mark.asyncio
    async def test_update_current_user_success(self, client, mock_user_repo, mock_current_user):
        """Test successful user update"""
        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = None
            mock_user_repo.update_user.return_value = {
                **mock_current_user,
                "email": "new@example.com",
                "language": "es"
            }

            update_data = UserUpdate(email="new@example.com", language="es")
            response = client.put("/api/v1/users/me", json=update_data.model_dump())

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "new@example.com"
            assert data["language"] == "es"
            mock_user_repo.update_user.assert_called_once_with(1, {"email": "new@example.com", "language": "es"})

    @pytest.mark.asyncio
    async def test_update_current_user_email_exists(self, client, mock_user_repo, mock_current_user):
        """Test update user with existing email"""
        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = {"id": 2, "email": "existing@example.com"}

            update_data = UserUpdate(email="existing@example.com")
            response = client.put("/api/v1/users/me", json=update_data.model_dump())

            assert response.status_code == 400
            assert "Email already registered" in response.json()["detail"]


    @pytest.mark.asyncio
    async def test_update_current_user_partial_update(self, client, mock_user_repo, mock_current_user):
        """Test partial user update"""
        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.users.get_current_user', return_value=mock_current_user):

            mock_user_repo.update_user.return_value = {**mock_current_user, "language": "de"}

            update_data = UserUpdate(language="de")
            response = client.put("/api/v1/users/me", json=update_data.model_dump())

            assert response.status_code == 200
            data = response.json()
            assert data["language"] == "de"
            mock_user_repo.update_user.assert_called_once_with(1, {"language": "de"})

    @pytest.mark.asyncio
    async def test_update_current_user_update_fails(self, client, mock_user_repo, mock_current_user):
        """Test update user when update fails"""
        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo):

            mock_user_repo.get_user_by_email.return_value = None
            mock_user_repo.update_user.return_value = None

            update_data = UserUpdate(language="fr")
            response = client.put("/api/v1/users/me", json=update_data.model_dump())

            assert response.status_code == 500
            assert "Failed to update user" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_current_user_database_exception(self, client, mock_user_repo, mock_current_user):
        """Test update user with database exception"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.users.get_current_user', return_value=mock_current_user):

            mock_user_repo.update_user.side_effect = DatabaseException("DB error")

            update_data = UserUpdate(language="fr")
            response = client.put("/api/v1/users/me", json=update_data.model_dump())

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_current_user_success(self, client, mock_user_repo, mock_current_user):
        """Test successful user deletion"""
        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.users.get_current_user', return_value=mock_current_user):

            mock_user_repo.delete_user.return_value = True

            response = client.delete("/api/v1/users/me")

            assert response.status_code == 204
            mock_user_repo.delete_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_current_user_fails(self, client, mock_user_repo, mock_current_user):
        """Test delete user when deletion fails"""
        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.users.get_current_user', return_value=mock_current_user):

            mock_user_repo.delete_user.return_value = False

            response = client.delete("/api/v1/users/me")

            assert response.status_code == 500
            assert "Failed to delete user" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_current_user_database_exception(self, client, mock_user_repo, mock_current_user):
        """Test delete user with database exception"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.users.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.users.get_current_user', return_value=mock_current_user):

            mock_user_repo.delete_user.side_effect = DatabaseException("DB error")

            response = client.delete("/api/v1/users/me")

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_rss_items_success(self, client, mock_rss_item_repo, mock_current_user):
        """Test successful get user RSS items"""
        with patch('apps.api.routers.users.get_service', return_value=mock_rss_item_repo), \
             patch('apps.api.routers.users.validate_rss_items_query_params', return_value=(None, None)), \
             patch('apps.api.routers.users.sanitize_search_phrase', return_value="sanitized"), \
             patch('apps.api.routers.users.process_rss_items_results', return_value=[{
                 "news_id": "1",
                 "original_title": "Test",
                 "original_content": "Content",
                 "original_language": "en"
             }]):

            mock_rss_item_repo.get_user_rss_items_list.return_value = (1, [("data",)], ["col1", "col2"])

            response = client.get("/api/v1/users/me/rss-items/")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert len(data["results"]) == 1

    @pytest.mark.asyncio
    async def test_get_user_rss_items_with_params(self, client, mock_rss_item_repo, mock_current_user):
        """Test get user RSS items with query parameters"""
        with patch('apps.api.routers.users.get_service', return_value=mock_rss_item_repo), \
             patch('apps.api.routers.users.validate_rss_items_query_params', return_value=(datetime.now(timezone.utc), None)), \
             patch('apps.api.routers.users.sanitize_search_phrase', return_value="test search"), \
             patch('apps.api.routers.users.process_rss_items_results', return_value=[]):

            mock_rss_item_repo.get_user_rss_items_list.return_value = (0, [], [])

            response = client.get("/api/v1/users/me/rss-items/?display_language=ru&searchPhrase=test&limit=10&offset=5")

            assert response.status_code == 200
            mock_rss_item_repo.get_user_rss_items_list.assert_called_once_with(1, "ru", None, 10, 5)

    @pytest.mark.asyncio
    async def test_get_user_rss_items_exception(self, client, mock_rss_item_repo, mock_current_user):
        """Test get user RSS items with exception"""
        with patch('apps.api.routers.users.get_service', return_value=mock_rss_item_repo), \
             patch('apps.api.routers.users.validate_rss_items_query_params', return_value=(None, None)), \
             patch('apps.api.routers.users.sanitize_search_phrase', return_value=None):

            mock_rss_item_repo.get_user_rss_items_list.side_effect = Exception("DB error")

            response = client.get("/api/v1/users/me/rss-items/")

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]