import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from repositories.user_repository import UserRepository
from exceptions import DatabaseException


@pytest.fixture
def user_repo(mock_db_pool):
    return UserRepository(mock_db_pool)


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_repo, mock_db_pool):
        """Test successful get user by email"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock
        
        cur.fetchone.return_value = (1, "test@example.com", "hash", "en", True, True, False, datetime.now(timezone.utc), None)

        result = await user_repo.get_user_by_email("test@example.com")

        assert result["id"] == 1
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_repo, mock_db_pool):
        """Test get user by email when not found"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = None

        result = await user_repo.get_user_by_email("notfound@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_database_error(self, user_repo, mock_db_pool):
        """Test get user by email with database error"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.execute.side_effect = Exception("DB error")

        with pytest.raises(DatabaseException):
            await user_repo.get_user_by_email("test@example.com")

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repo, mock_db_pool):
        """Test successful user creation"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = (1, "test@example.com", "en", True, True, datetime.now(timezone.utc))

        result = await user_repo.create_user("test@example.com", "hash", "en")

        assert result["id"] == 1
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repo, mock_db_pool):
        """Test successful user update"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = (1, "new@example.com", "es", True, True, datetime.now(timezone.utc))

        result = await user_repo.update_user(1, {"email": "new@example.com", "language": "es"})

        assert result["email"] == "new@example.com"
        assert result["language"] == "es"

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repo, mock_db_pool):
        """Test successful user deletion"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.rowcount = 1

        result = await user_repo.delete_user(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_activate_user_and_use_verification_code_success(self, user_repo, mock_db_pool):
        """Test successful user activation with verification code"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = (1,)  # verification_row

        result = await user_repo.activate_user_and_use_verification_code(1, "123456")

        assert result is True

    @pytest.mark.asyncio
    async def test_activate_user_and_use_verification_code_invalid_code(self, user_repo, mock_db_pool):
        """Test user activation with invalid verification code"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = None  # no verification row

        result = await user_repo.activate_user_and_use_verification_code(1, "invalid")

        assert result is False

    @pytest.mark.asyncio
    async def test_confirm_password_reset_transaction_success(self, user_repo, mock_db_pool):
        """Test successful password reset confirmation"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = (1,)  # user_id

        result = await user_repo.confirm_password_reset_transaction("token", "new_hash")

        assert result is True

    @pytest.mark.asyncio
    async def test_confirm_password_reset_transaction_invalid_token(self, user_repo, mock_db_pool):
        """Test password reset confirmation with invalid token"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = None  # no reset row

        result = await user_repo.confirm_password_reset_transaction("invalid_token", "new_hash")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_telegram_user_settings_success(self, user_repo, mock_db_pool):
        """Test successful get Telegram user settings"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = ('["tech", "sports"]', "ru")

        result = await user_repo.get_telegram_user_settings(123)

        assert result["subscriptions"] == ["tech", "sports"]
        assert result["language"] == "ru"

    @pytest.mark.asyncio
    async def test_get_telegram_user_settings_no_settings(self, user_repo, mock_db_pool):
        """Test get Telegram user settings when no settings exist"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = None

        result = await user_repo.get_telegram_user_settings(123)

        assert result["subscriptions"] == []
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_generate_telegram_link_code_success(self, user_repo, mock_db_pool):
        """Test successful generation of Telegram link code"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        result = await user_repo.generate_telegram_link_code(1)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_confirm_telegram_link_success(self, user_repo, mock_db_pool):
        """Test successful Telegram link confirmation"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.side_effect = [(1,), None]  # user_id found, telegram_id not linked

        result = await user_repo.confirm_telegram_link(12345, "link_code")

        assert result is True

    @pytest.mark.asyncio
    async def test_confirm_telegram_link_already_linked(self, user_repo, mock_db_pool):
        """Test Telegram link confirmation when already linked"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.side_effect = [(1,), (1,)]  # user_id found, telegram_id already linked

        result = await user_repo.confirm_telegram_link(12345, "link_code")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_success(self, user_repo, mock_db_pool):
        """Test successful get user by Telegram ID"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = (1, "test@example.com", "hash", "en", True, True, False, datetime.now(timezone.utc), None)
        cur.description = [("id",), ("email",), ("password_hash",), ("language",), ("is_active",), ("is_verified",), ("is_deleted",), ("created_at",), ("updated_at",)]

        result = await user_repo.get_user_by_telegram_id(12345)

        assert result["id"] == 1
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_not_found(self, user_repo, mock_db_pool):
        """Test get user by Telegram ID when not found"""
        # Get the mocked connection and cursor from the fixture
        conn = mock_db_pool.acquire.return_value.return_value
        cur = conn.cursor_mock

        cur.fetchone.return_value = None

        result = await user_repo.get_user_by_telegram_id(12345)

        assert result is None