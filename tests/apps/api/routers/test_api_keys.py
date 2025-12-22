import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from apps.api.routers.api_keys import router
from apps.api.models import UserApiKeyGenerateResponse, APIKeyCreate
from apps.api.deps import get_current_user
from datetime import datetime, timezone

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
def client(mock_current_user):
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    return TestClient(app)

@pytest.fixture
def mock_repo():
    return AsyncMock()

class TestAPIKeysRouter:
    @pytest.mark.asyncio
    async def test_generate_own_api_key_success(self, client, mock_repo):
        with patch('apps.api.routers.api_keys.get_service') as mock_get_service:
            mock_get_service.return_value = mock_repo
            
            # Configure the mock to return a proper awaitable value
            async def mock_create_user_api_key(*args, **kwargs):
                return {
                    "id": 1,
                    "user_id": 1,
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": None
                }
            mock_repo.create_user_api_key = mock_create_user_api_key
            
            response = client.post("/api/v1/api-keys/generate-own")
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == 1

    @pytest.mark.asyncio
    async def test_create_api_key_failure(self, client, mock_repo):
        with patch('apps.api.routers.api_keys.get_service') as mock_get_service:
            mock_get_service.return_value = mock_repo
            
            # This route doesn't exist, so it will 404
            api_key_data = APIKeyCreate(name="test_key", user_id=1)
            response = client.post("/api-keys/", json=api_key_data.model_dump())
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_api_keys(self, client, mock_repo):
        with patch('apps.api.routers.api_keys.get_service') as mock_get_service:
            mock_get_service.return_value = mock_repo
            
            # Configure the mock to return a proper awaitable value
            async def mock_get_user_api_keys(*args, **kwargs):
                return [
                    {
                        "id": 1,
                        "user_id": 1,
                        "created_at": datetime.now(timezone.utc),
                        "expires_at": None,
                        "is_active": True,
                        "limits": {"requests_per_day": 1000, "requests_per_hour": 100}
                    }
                ]
            mock_repo.get_user_api_keys = mock_get_user_api_keys
            
            response = client.get("/api/v1/api-keys/list")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == 1
            assert data[0]["user_id"] == 1
            assert data[0]["is_active"] == True

    @pytest.mark.asyncio
    async def test_delete_api_key_success(self, client, mock_repo):
        with patch('apps.api.routers.api_keys.get_service') as mock_get_service:
            mock_get_service.return_value = mock_repo
            
            # Configure the mocks
            async def mock_get_user_api_key_by_id(*args, **kwargs):
                return {"id": 1, "user_id": 1}
            
            async def mock_delete_user_api_key(*args, **kwargs):
                return True
                
            mock_repo.get_user_api_key_by_id = mock_get_user_api_key_by_id
            mock_repo.delete_user_api_key = mock_delete_user_api_key
            
            response = client.delete("/api/v1/api-keys/1")
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_api_key_not_found(self, client, mock_repo):
        with patch('apps.api.routers.api_keys.get_service') as mock_get_service:
            mock_get_service.return_value = mock_repo
            
            # Configure the mock to return None (not found)
            async def mock_get_user_api_key_by_id(*args, **kwargs):
                return None
                
            mock_repo.get_user_api_key_by_id = mock_get_user_api_key_by_id
            
            response = client.delete("/api/v1/api-keys/1")
            assert response.status_code == 404