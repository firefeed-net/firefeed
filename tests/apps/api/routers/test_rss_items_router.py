import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from apps.api.routers.rss_items import router
from apps.api.deps import get_current_user_by_api_key


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
    app.dependency_overrides[get_current_user_by_api_key] = lambda: mock_current_user
    return TestClient(app)


class TestRSSItemsRouter:
    @pytest.mark.asyncio
    async def test_get_rss_items_success(self, client):
        with patch('apps.api.routers.rss_items.get_service') as mock_get_service, \
             patch('apps.api.routers.rss_items.validate_rss_items_query_params') as mock_validate, \
             patch('apps.api.routers.rss_items.process_rss_items_results') as mock_process:

            mock_repo = AsyncMock()
            mock_repo.get_all_rss_items_list.return_value = (10, [], [])
            mock_get_service.return_value = mock_repo
            mock_validate.return_value = ("2023-01-01", None)
            mock_process.return_value = []

            response = client.get("/api/v1/rss-items/")

            assert response.status_code == 200
            data = response.json()
            assert "count" in data
            assert "results" in data

    @pytest.mark.asyncio
    async def test_get_rss_item_by_id_success(self, client):
        with patch('apps.api.routers.rss_items.get_service') as mock_get_service, \
             patch('apps.api.routers.rss_items.get_full_image_url') as mock_get_image_url, \
             patch('apps.api.routers.rss_items.format_datetime') as mock_format_datetime:

            mock_repo = AsyncMock()
            # Add translation columns that build_translations_dict expects
            row_data = ("news123", "Title", "Content", "en", "image.jpg", "Tech", "Source", "src", "http://source.com", "2023-01-01", "embed123", "Title", "Content", None, None, None, None, None, None)  # Add translation columns
            columns = ["news_id", "original_title", "original_content", "original_language", "image_filename", "category_name", "source_name", "source_alias", "source_url", "created_at", "embedding", "title_ru", "content_ru", "title_de", "content_de", "title_fr", "content_fr", "title_en", "content_en"]
            mock_repo.get_rss_item_by_id_full.return_value = (row_data, columns)
            mock_get_service.return_value = mock_repo
            mock_get_image_url.return_value = "http://image.com"
            mock_format_datetime.return_value = "2023-01-01T00:00:00Z"

            response = client.get("/api/v1/rss-items/news123")

            assert response.status_code == 200
            data = response.json()
            assert data["news_id"] == "news123"

    @pytest.mark.asyncio
    async def test_get_rss_item_by_id_not_found(self, client):
        with patch('apps.api.routers.rss_items.get_service') as mock_get_service:

            mock_repo = AsyncMock()
            mock_repo.get_rss_item_by_id_full.return_value = None
            mock_get_service.return_value = mock_repo

            response = client.get("/api/v1/rss-items/nonexistent")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_categories_success(self, client):
        with patch('apps.api.routers.rss_items.get_service') as mock_get_service:

            mock_repo = AsyncMock()
            mock_repo.get_all_categories_list.return_value = (5, [{"id": 1, "name": "Tech"}])
            mock_get_service.return_value = mock_repo

            response = client.get("/api/v1/categories/")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 5
            assert len(data["results"]) == 1

    @pytest.mark.asyncio
    async def test_get_sources_success(self, client):
        with patch('apps.api.routers.rss_items.get_service') as mock_get_service:

            mock_repo = AsyncMock()
            mock_repo.get_all_sources_list.return_value = (10, [{"id": 1, "name": "BBC", "alias": "bbc"}])
            mock_get_service.return_value = mock_repo

            response = client.get("/api/v1/sources/")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 10
            assert len(data["results"]) == 1

    @pytest.mark.asyncio
    async def test_get_languages_success(self, client):
        with patch('apps.api.routers.rss_items.get_service') as mock_get_service:

            mock_config = {"SUPPORTED_LANGUAGES": ["en", "ru", "de", "fr"]}
            mock_get_service.return_value = mock_config

            response = client.get("/api/v1/languages/")

            assert response.status_code == 200
            data = response.json()
            assert data["results"] == ["en", "ru", "de", "fr"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        with patch('apps.api.routers.rss_items.get_service') as mock_get_service:

            mock_user_repo = AsyncMock()
            mock_pool_adapter = AsyncMock()
            mock_pool_adapter._pool.size = 20
            mock_pool_adapter._pool.freesize = 15
            mock_user_repo.db_pool = mock_pool_adapter
            mock_get_service.return_value = mock_user_repo

            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["database"] == "ok"
            assert data["db_pool"]["total_connections"] == 20
            assert data["db_pool"]["free_connections"] == 15