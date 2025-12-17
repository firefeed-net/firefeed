# tests/test_user_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.user.telegram_user_service import TelegramUserService
from services.user.web_user_service import WebUserService
from interfaces import ITelegramUserService, IWebUserService


class TestTelegramUserService:
    """Test TelegramUserService"""

    @pytest.fixture
    def service(self):
        from unittest.mock import AsyncMock
        return TelegramUserService(user_repository=AsyncMock())

    @pytest.fixture
    def mock_pool(self):
        pool = AsyncMock()
        return pool

    @pytest.fixture
    def mock_conn(self):
        conn = AsyncMock()
        return conn

    @pytest.fixture
    def mock_cur(self):
        cur = AsyncMock()
        return cur

    @pytest.mark.asyncio
    async def test_get_user_settings_success(self, service):
        """Test getting user settings successfully"""
        service.user_repository.get_telegram_user_settings = AsyncMock(return_value={"subscriptions": ["tech", "sports"], "language": "en"})

        result = await service.get_user_settings(123)

        assert result == {"subscriptions": ["tech", "sports"], "language": "en"}
        service.user_repository.get_telegram_user_settings.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_get_user_settings_not_found(self, service):
        """Test getting user settings when not found"""
        service.user_repository.get_telegram_user_settings = AsyncMock(return_value=None)

        result = await service.get_user_settings(123)

        assert result is None
        service.user_repository.get_telegram_user_settings.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_save_user_settings_success(self, service):
        """Test saving user settings successfully"""
        service.user_repository.save_telegram_user_settings = AsyncMock(return_value=True)

        result = await service.save_user_settings(123, ["tech"], "en")

        assert result is True
        service.user_repository.save_telegram_user_settings.assert_called_once_with(123, ["tech"], "en")

    @pytest.mark.asyncio
    async def test_set_user_language_success(self, service):
        """Test setting user language successfully"""
        service.user_repository.set_telegram_user_language = AsyncMock(return_value=True)

        result = await service.set_user_language(123, "ru")

        assert result is True
        service.user_repository.set_telegram_user_language.assert_called_once_with(123, "ru")

    @pytest.mark.asyncio
    async def test_get_subscribers_for_category(self, service):
        """Test getting subscribers for category"""
        service.user_repository.get_telegram_subscribers_for_category = AsyncMock(return_value=[
            {"id": 1, "subscriptions": ["tech", "sports"], "language": "en"},
            {"id": 2, "subscriptions": ["tech"], "language": "ru"}
        ])

        result = await service.get_subscribers_for_category("tech")

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        service.user_repository.get_telegram_subscribers_for_category.assert_called_once_with("tech")

    @pytest.mark.asyncio
    async def test_get_all_users(self, service):
        """Test getting all users"""
        service.user_repository.get_all_telegram_users = AsyncMock(return_value=[1, 2])

        result = await service.get_all_users()

        assert result == [1, 2]
        service.user_repository.get_all_telegram_users.assert_called_once()

    def test_implements_interface(self, service):
        """Test that service implements the interface"""
        assert isinstance(service, ITelegramUserService)


class TestWebUserService:
    """Test WebUserService"""

    @pytest.fixture
    def service(self):
        from unittest.mock import AsyncMock
        return WebUserService(user_repository=AsyncMock())

    @pytest.fixture
    def mock_pool(self):
        pool = AsyncMock()
        return pool

    @pytest.fixture
    def mock_conn(self):
        conn = AsyncMock()
        return conn

    @pytest.fixture
    def mock_cur(self):
        cur = AsyncMock()
        return cur

    @pytest.mark.asyncio
    async def test_generate_telegram_link_code(self, service):
        """Test generating Telegram link code"""
        service.user_repository.generate_telegram_link_code = AsyncMock(return_value='test_code_123')

        result = await service.generate_telegram_link_code(123)

        assert result == 'test_code_123'
        service.user_repository.generate_telegram_link_code.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_confirm_telegram_link_success(self, service):
        """Test confirming Telegram link successfully"""
        service.user_repository.confirm_telegram_link = AsyncMock(return_value=True)

        result = await service.confirm_telegram_link(456, 'test_code')

        assert result is True
        service.user_repository.confirm_telegram_link.assert_called_once_with(456, 'test_code')

    @pytest.mark.asyncio
    async def test_confirm_telegram_link_invalid_code(self, service):
        """Test confirming Telegram link with invalid code"""
        service.user_repository.confirm_telegram_link = AsyncMock(return_value=False)

        result = await service.confirm_telegram_link(456, 'invalid_code')

        assert result is False
        service.user_repository.confirm_telegram_link.assert_called_once_with(456, 'invalid_code')

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_found(self, service):
        """Test getting user by Telegram ID when found"""
        service.user_repository.get_user_by_telegram_id.return_value = {"id": 123, "email": "user@example.com", "password_hash": "hash", "language": "en", "is_active": True, "created_at": None, "updated_at": None}

        result = await service.get_user_by_telegram_id(456)

        assert result is not None
        assert result['id'] == 123
        service.user_repository.get_user_by_telegram_id.assert_called_once_with(456)

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_not_found(self, service):
        """Test getting user by Telegram ID when not found"""
        service.user_repository.get_user_by_telegram_id.return_value = None

        result = await service.get_user_by_telegram_id(456)

        assert result is None
        service.user_repository.get_user_by_telegram_id.assert_called_once_with(456)

    @pytest.mark.asyncio
    async def test_unlink_telegram_success(self, service):
        """Test unlinking Telegram successfully"""
        service.user_repository.unlink_telegram.return_value = True

        result = await service.unlink_telegram(123)

        assert result is True
        service.user_repository.unlink_telegram.assert_called_once_with(123)

    def test_implements_interface(self, service):
        """Test that service implements the interface"""
        assert isinstance(service, IWebUserService)


class TestDIIntegration:
    """Test DI container integration"""

    @pytest.mark.asyncio
    async def test_services_registered_in_di(self):
        """Test that user services are registered in DI container"""
        from di_container import di_container, setup_di_container

        # Setup DI container
        await setup_di_container()

        # Test that we can resolve user services
        telegram_service = di_container.resolve(ITelegramUserService)
        web_service = di_container.resolve(IWebUserService)

        assert isinstance(telegram_service, ITelegramUserService)
        assert isinstance(web_service, IWebUserService)