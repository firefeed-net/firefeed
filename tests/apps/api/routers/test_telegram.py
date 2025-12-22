import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from apps.api.routers.telegram import router
from apps.api.deps import get_current_user
from interfaces import IUserService

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
def client_with_auth(mock_current_user):
    from fastapi import FastAPI
    from apps.api.deps import get_current_user
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    return TestClient(app)

@pytest.fixture
def mock_service():
    return AsyncMock()

class TestTelegramRouter:
    @pytest.mark.asyncio
    async def test_get_telegram_status_success(self, client_with_auth, mock_service):
        with patch('di_container.get_service') as mock_get_service:
            def mock_get_service_side_effect(interface):
                if interface == IUserService:
                    return mock_service
                return AsyncMock()
            
            mock_get_service.side_effect = mock_get_service_side_effect
            mock_service.get_telegram_link_status.return_value = {
                "telegram_id": 12345,
                "linked_at": "2023-01-01T00:00:00Z"
            }
            response = client_with_auth.get("/api/v1/users/me/telegram/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_linked"] == True
            assert data["telegram_id"] == 12345
            mock_service.get_telegram_link_status.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_telegram_status_not_linked(self, client_with_auth, mock_service):
        with patch('di_container.get_service') as mock_get_service:
            def mock_get_service_side_effect(interface):
                if interface == IUserService:
                    return mock_service
                return AsyncMock()
            
            mock_get_service.side_effect = mock_get_service_side_effect
            mock_service.get_telegram_link_status.return_value = None
            response = client_with_auth.get("/api/v1/users/me/telegram/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_linked"] == False
            assert data["telegram_id"] is None
            mock_service.get_telegram_link_status.assert_called_once_with(1)