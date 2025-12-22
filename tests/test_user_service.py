import pytest
from unittest.mock import AsyncMock
from services.user.user_service import UserService


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_user_repo):
    return UserService(mock_user_repo)


class TestUserService:
    @pytest.mark.asyncio
    async def test_generate_telegram_link_code(self, service, mock_user_repo):
        mock_user_repo.generate_telegram_link_code.return_value = "ABC123"

        result = await service.generate_telegram_link_code(1)

        assert result == "ABC123"
        mock_user_repo.generate_telegram_link_code.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_confirm_telegram_link(self, service, mock_user_repo):
        mock_user_repo.confirm_telegram_link.return_value = True

        result = await service.confirm_telegram_link(12345, "ABC123")

        assert result is True
        mock_user_repo.confirm_telegram_link.assert_called_once_with(12345, "ABC123")

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id(self, service, mock_user_repo):
        user_data = {"id": 1, "email": "test@example.com"}
        mock_user_repo.get_user_by_telegram_id.return_value = user_data

        result = await service.get_user_by_telegram_id(12345)

        assert result == user_data
        mock_user_repo.get_user_by_telegram_id.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_unlink_telegram(self, service, mock_user_repo):
        mock_user_repo.unlink_telegram.return_value = True

        result = await service.unlink_telegram(1)

        assert result is True
        mock_user_repo.unlink_telegram.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_telegram_link_status(self, service, mock_user_repo):
        status_data = {"linked": True, "telegram_id": 12345}
        mock_user_repo.get_telegram_link_status.return_value = status_data

        result = await service.get_telegram_link_status(1)

        assert result == status_data
        mock_user_repo.get_telegram_link_status.assert_called_once_with(1)