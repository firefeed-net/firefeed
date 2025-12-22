import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, Request
from apps.api.routers.categories import get_user_categories, update_user_categories
from apps.api.models import UserCategoriesUpdate


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
def mock_category_repo():
    return AsyncMock()


class TestCategoriesRouter:
    @pytest.mark.asyncio
    async def test_get_user_categories_success(self, mock_current_user, mock_category_repo):
        """Test successful get user categories"""
        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_user_categories.return_value = [
                {"id": 1, "name": "Technology"},
                {"id": 2, "name": "Sports"}
            ]

            request = Request(scope={"type": "http", "method": "GET", "path": "/"})
            result = await get_user_categories(request, current_user=mock_current_user)

            assert result.category_ids == [1, 2]
            mock_category_repo.get_user_categories.assert_called_once()
            args = mock_category_repo.get_user_categories.call_args[0]
            assert args[0] == 1  # user_id
            # source_ids is Query(None) by default

    @pytest.mark.asyncio
    async def test_get_user_categories_with_source_filter(self, mock_current_user, mock_category_repo):
        """Test get user categories with source filter"""
        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_user_categories.return_value = [
                {"id": 1, "name": "Technology"}
            ]

            request = Request(scope={"type": "http", "method": "GET", "path": "/"})
            result = await get_user_categories(request, current_user=mock_current_user, source_ids=[1, 2])

            assert result.category_ids == [1]
            mock_category_repo.get_user_categories.assert_called_once_with(1, [1, 2])

    @pytest.mark.asyncio
    async def test_update_user_categories_success(self, mock_current_user, mock_category_repo):
        """Test successful update user categories"""
        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_all_category_ids.return_value = [1, 2, 3]
            mock_category_repo.update_user_categories.return_value = True

            update_data = UserCategoriesUpdate(category_ids={1, 2})
            request = Request(scope={"type": "http", "method": "PUT", "path": "/"})
            result = await update_user_categories(request, update_data, mock_current_user)

            assert result.message == "User categories successfully updated"
            mock_category_repo.update_user_categories.assert_called_once_with(1, [1, 2])

    @pytest.mark.asyncio
    async def test_update_user_categories_invalid_ids(self, mock_current_user, mock_category_repo):
        """Test update user categories with invalid category IDs"""
        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_all_category_ids.return_value = [1, 2]  # Only 1 and 2 exist

            update_data = UserCategoriesUpdate(category_ids={1, 2, 99})  # 99 is invalid

            with pytest.raises(HTTPException) as exc_info:
                request = Request(scope={"type": "http", "method": "PUT", "path": "/"})
                await update_user_categories(request, update_data, mock_current_user)

            assert exc_info.value.status_code == 400
            assert "Invalid category IDs: [99]" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_user_categories_update_fails(self, mock_current_user, mock_category_repo):
        """Test update user categories when update fails"""
        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_all_category_ids.return_value = [1, 2, 3]
            mock_category_repo.update_user_categories.return_value = False

            update_data = UserCategoriesUpdate(category_ids={1, 2})

            request = Request(scope={"type": "http", "method": "PUT", "path": "/"})
            with pytest.raises(HTTPException) as exc_info:
                await update_user_categories(request, update_data, mock_current_user)

            assert exc_info.value.status_code == 500
            assert "Failed to update user categories" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_user_categories_empty(self, mock_current_user, mock_category_repo):
        """Test get user categories when no categories"""
        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_user_categories.return_value = []

            result = await get_user_categories(Request(scope={"type": "http", "method": "GET", "path": "/"}), current_user=mock_current_user)

            assert result.category_ids == []

    @pytest.mark.asyncio
    async def test_get_user_categories_database_error(self, mock_current_user, mock_category_repo):
        """Test get user categories with database error"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):
            mock_category_repo.get_user_categories.side_effect = DatabaseException("DB error")

            request = Request(scope={"type": "http", "method": "GET", "path": "/"})
            with pytest.raises(HTTPException) as exc_info:
                await get_user_categories(request, current_user=mock_current_user)

            assert exc_info.value.status_code == 500
            assert "Database error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_user_categories_partial_update(self, mock_current_user, mock_category_repo):
        """Test partial update user categories"""
        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_all_category_ids.return_value = [1, 2, 3]
            mock_category_repo.update_user_categories.return_value = True

            update_data = UserCategoriesUpdate(category_ids={1})  # Only update some categories
            result = await update_user_categories(Request(scope={"type": "http", "method": "PUT", "path": "/"}), update_data, mock_current_user)

            assert result.message == "User categories successfully updated"
            mock_category_repo.update_user_categories.assert_called_once_with(1, [1])

    @pytest.mark.asyncio
    async def test_update_user_categories_database_error(self, mock_current_user, mock_category_repo):
        """Test update user categories with database error"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.categories.get_service', return_value=mock_category_repo):

            mock_category_repo.get_all_category_ids.return_value = [1, 2, 3]
            mock_category_repo.update_user_categories.side_effect = DatabaseException("DB error")

            update_data = UserCategoriesUpdate(category_ids={1, 2})

            request = Request(scope={"type": "http", "method": "PUT", "path": "/"})
            with pytest.raises(HTTPException) as exc_info:
                await update_user_categories(request, update_data, mock_current_user)

            assert exc_info.value.status_code == 500
            assert "Database error" in exc_info.value.detail