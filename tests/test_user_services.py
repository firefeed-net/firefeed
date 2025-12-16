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
        return TelegramUserService()

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

    async def test_get_user_settings_success(self, service, mock_pool, mock_conn, mock_cur):
        """Test getting user settings successfully"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (["tech", "sports"], "en")

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.get_user_settings(123)

        assert result == {"subscriptions": ["tech", "sports"], "language": "en"}

    async def test_get_user_settings_not_found(self, service, mock_pool, mock_conn, mock_cur):
        """Test getting user settings when not found"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.get_user_settings(123)

        assert result == {"subscriptions": [], "language": "en"}

    async def test_save_user_settings_success(self, service, mock_pool, mock_conn, mock_cur):
        """Test saving user settings successfully"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.rowcount = 0  # No existing record

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.save_user_settings(123, ["tech"], "en")

        assert result is True

    async def test_set_user_language_success(self, service, mock_pool, mock_conn, mock_cur):
        """Test setting user language successfully"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.set_user_language(123, "ru")

        assert result is True

    async def test_get_subscribers_for_category(self, service, mock_pool, mock_conn, mock_cur):
        """Test getting subscribers for category"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[
            (1, '["tech", "sports"]', "en"),
            (2, '["tech"]', "ru"),
            None
        ])

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.get_subscribers_for_category("tech")

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    async def test_get_all_users(self, service, mock_pool, mock_conn, mock_cur):
        """Test getting all users"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[(1,), (2,), None])

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.get_all_users()

        assert result == [1, 2]

    def test_implements_interface(self, service):
        """Test that service implements the interface"""
        assert isinstance(service, ITelegramUserService)


class TestWebUserService:
    """Test WebUserService"""

    @pytest.fixture
    def service(self):
        return WebUserService()

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

    async def test_generate_telegram_link_code(self, service, mock_pool, mock_conn, mock_cur):
        """Test generating Telegram link code"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur

        with patch('secrets.token_urlsafe', return_value='test_code_123'):
            with patch.object(service, 'get_pool', return_value=mock_pool):
                result = await service.generate_telegram_link_code(123)

        assert result == 'test_code_123'

    async def test_confirm_telegram_link_success(self, service, mock_pool, mock_conn, mock_cur):
        """Test confirming Telegram link successfully"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (123,)  # user_id

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.confirm_telegram_link(456, 'test_code')

        assert result is True

    async def test_confirm_telegram_link_invalid_code(self, service, mock_pool, mock_conn, mock_cur):
        """Test confirming Telegram link with invalid code"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.confirm_telegram_link(456, 'invalid_code')

        assert result is False

    async def test_get_user_by_telegram_id_found(self, service, mock_pool, mock_conn, mock_cur):
        """Test getting user by Telegram ID when found"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (123, 'user@example.com', 'hash', 'en', True, None, None)
        mock_cur.description = [('id',), ('email',), ('password_hash',), ('language',), ('is_active',), ('created_at',), ('updated_at')]

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.get_user_by_telegram_id(456)

        assert result is not None
        assert result['id'] == 123

    async def test_get_user_by_telegram_id_not_found(self, service, mock_pool, mock_conn, mock_cur):
        """Test getting user by Telegram ID when not found"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.get_user_by_telegram_id(456)

        assert result is None

    async def test_unlink_telegram_success(self, service, mock_pool, mock_conn, mock_cur):
        """Test unlinking Telegram successfully"""
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.rowcount = 1

        with patch.object(service, 'get_pool', return_value=mock_pool):
            result = await service.unlink_telegram(123)

        assert result is True

    def test_implements_interface(self, service):
        """Test that service implements the interface"""
        assert isinstance(service, IWebUserService)


class TestDIIntegration:
    """Test DI container integration"""

    def test_services_registered_in_di(self):
        """Test that user services are registered in DI container"""
        from di_container import di_container, setup_di_container

        # Setup DI container
        setup_di_container()

        # Test that we can resolve user services
        telegram_service = di_container.resolve(ITelegramUserService)
        web_service = di_container.resolve(IWebUserService)

        assert isinstance(telegram_service, ITelegramUserService)
        assert isinstance(web_service, IWebUserService)