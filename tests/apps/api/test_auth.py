import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from apps.api.routers.auth import router
from apps.api.models import UserCreate, EmailVerificationRequest, ResendVerificationRequest, PasswordResetRequest, PasswordResetConfirm
from di_container import get_service


@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_email_sender():
    return AsyncMock()


class TestAuthRouter:
    @pytest.mark.asyncio
    async def test_register_user_success(self, client, mock_user_repo, mock_email_sender):
        """Test successful user registration"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.send_verification_email', mock_email_sender):

            mock_user_repo.get_user_by_email.return_value = None
            mock_user_repo.create_user.return_value = {
                "id": 1,
                "email": "test@example.com",
                "language": "en",
                "is_active": True,
                "is_verified": False,
                "is_deleted": False,
                "created_at": datetime.now(timezone.utc),
                "updated_at": None
            }
            mock_user_repo.save_verification_code.return_value = True

            user_data = UserCreate(email="test@example.com", password="password123", language="en")
            response = client.post("/api/v1/auth/register", json=user_data.model_dump())

            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "test@example.com"
            mock_user_repo.create_user.assert_called_once()
            mock_email_sender.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, client, mock_user_repo):
        """Test registration with existing email"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = {"id": 1, "email": "test@example.com"}

            user_data = UserCreate(email="test@example.com", password="password123", language="en")
            response = client.post("/api/v1/auth/register", json=user_data.model_dump())

            assert response.status_code == 400
            assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_user_create_fails(self, client, mock_user_repo):
        """Test registration when user creation fails"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = None
            mock_user_repo.create_user.return_value = None

            user_data = UserCreate(email="test@example.com", password="password123", language="en")
            response = client.post("/api/v1/auth/register", json=user_data.model_dump())

            assert response.status_code == 500
            assert "Failed to create user" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_user_success(self, client, mock_user_repo, mock_email_sender):
        """Test successful email verification"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.send_registration_success_email', mock_email_sender):

            mock_user_repo.get_user_by_email.return_value = {
                "id": 1,
                "email": "test@example.com",
                "is_verified": False,
                "language": "en",
                "is_active": True,
                "is_deleted": False,
                "created_at": datetime.now(timezone.utc)
            }
            mock_user_repo.activate_user_and_use_verification_code.return_value = True

            verification_data = EmailVerificationRequest(email="test@example.com", code="123456")
            response = client.post("/api/v1/auth/verify", json=verification_data.model_dump())

            assert response.status_code == 200
            assert response.json()["message"] == "User successfully verified"
            mock_email_sender.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_user_already_verified(self, client, mock_user_repo):
        """Test verification of already verified user"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = {"id": 1, "email": "test@example.com", "is_verified": True}

            verification_data = EmailVerificationRequest(email="test@example.com", code="123456")
            response = client.post("/api/v1/auth/verify", json=verification_data.model_dump())

            assert response.status_code == 400
            assert "User already verified" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_user_database_exception(self, client, mock_user_repo):
        """Test register_user with database exception"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = None
            mock_user_repo.create_user.side_effect = DatabaseException("DB error")

            user_data = UserCreate(email="test@example.com", password="password123", language="en")
            response = client.post("/api/v1/auth/register", json=user_data.model_dump())

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_user_database_exception(self, client, mock_user_repo):
        """Test verify_user with database exception"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.side_effect = DatabaseException("DB error")

            verification_data = EmailVerificationRequest(email="test@example.com", code="123456")
            response = client.post("/api/v1/auth/verify", json=verification_data.model_dump())

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_database_exception(self, client, mock_user_repo):
        """Test login with database exception"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.side_effect = DatabaseException("DB error")

            response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"})

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_user_deleted(self, client, mock_user_repo):
        """Test login with deleted user"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.verify_password', return_value=True):

            mock_user_repo.get_user_by_email.return_value = {
                "id": 1,
                "email": "test@example.com",
                "password_hash": "hashed",
                "is_verified": True,
                "is_deleted": True
            }

            response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"})

            assert response.status_code == 401
            assert "Account deactivated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_request_password_reset_database_exception(self, client, mock_user_repo):
        """Test request_password_reset with database exception"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = {"id": 1, "email": "test@example.com", "language": "en"}
            mock_user_repo.save_password_reset_token.side_effect = DatabaseException("DB error")

            reset_data = PasswordResetRequest(email="test@example.com")
            response = client.post("/api/v1/auth/reset-password/request", json=reset_data.model_dump())

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_confirm_password_reset_database_exception(self, client, mock_user_repo):
        """Test confirm_password_reset with database exception"""
        from exceptions import DatabaseException

        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.get_password_hash', return_value="new_hash"):

            mock_user_repo.confirm_password_reset_transaction.side_effect = DatabaseException("DB error")

            confirm_data = PasswordResetConfirm(token="valid_token", new_password="newpassword123")
            response = client.post("/api/v1/auth/reset-password/confirm", json=confirm_data.model_dump())

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_user_invalid_code(self, client, mock_user_repo):
        """Test verification with invalid code"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = {"id": 1, "email": "test@example.com", "is_verified": False}
            mock_user_repo.activate_user_and_use_verification_code.return_value = False

            verification_data = EmailVerificationRequest(email="test@example.com", code="123456")
            response = client.post("/api/v1/auth/verify", json=verification_data.model_dump())

            assert response.status_code == 400
            assert "Invalid verification code" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client, mock_user_repo):
        """Test successful login"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.verify_password', return_value=True), \
             patch('apps.api.routers.auth.create_access_token', return_value="fake_token"):

            mock_user_repo.get_user_by_email.return_value = {
                "id": 1,
                "email": "test@example.com",
                "password_hash": "hashed",
                "is_verified": True,
                "is_deleted": False
            }

            response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"})

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, mock_user_repo):
        """Test login with invalid credentials"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = None

            response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "wrong"})

            assert response.status_code == 401
            assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_unverified_account(self, client, mock_user_repo):
        """Test login with unverified account"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.verify_password', return_value=True):

            mock_user_repo.get_user_by_email.return_value = {
                "id": 1,
                "email": "test@example.com",
                "password_hash": "hashed",
                "is_verified": False,
                "is_deleted": False
            }

            response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"})

            assert response.status_code == 401
            assert "Account not verified" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_request_password_reset_success(self, client, mock_user_repo, mock_email_sender):
        """Test successful password reset request"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.send_password_reset_email', mock_email_sender):

            mock_user_repo.get_user_by_email.return_value = {"id": 1, "email": "test@example.com", "language": "en"}
            mock_user_repo.save_password_reset_token.return_value = True

            reset_data = PasswordResetRequest(email="test@example.com")
            response = client.post("/api/v1/auth/reset-password/request", json=reset_data.model_dump())

            assert response.status_code == 200
            assert "reset instructions have been sent" in response.json()["message"]
            mock_email_sender.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_email_not_found(self, client, mock_user_repo):
        """Test password reset request for non-existent email"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = None

            reset_data = PasswordResetRequest(email="nonexistent@example.com")
            response = client.post("/api/v1/auth/reset-password/request", json=reset_data.model_dump())

            assert response.status_code == 200
            assert "reset instructions have been sent" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(self, client, mock_user_repo):
        """Test successful password reset confirmation"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.get_password_hash', return_value="new_hash"):

            mock_user_repo.confirm_password_reset_transaction.return_value = True

            confirm_data = PasswordResetConfirm(token="valid_token", new_password="newpassword123")
            response = client.post("/api/v1/auth/reset-password/confirm", json=confirm_data.model_dump())

            assert response.status_code == 200
            assert "Password successfully reset" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(self, client, mock_user_repo):
        """Test password reset confirmation with invalid token"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.get_password_hash', return_value="new_hash"):

            mock_user_repo.confirm_password_reset_transaction.return_value = False

            confirm_data = PasswordResetConfirm(token="invalid_token", new_password="newpassword123")
            response = client.post("/api/v1/auth/reset-password/confirm", json=confirm_data.model_dump())

            assert response.status_code == 400
            assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_resend_verification_success(self, client, mock_user_repo, mock_email_sender):
        """Test successful resend verification"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo), \
             patch('apps.api.routers.auth.send_verification_email', mock_email_sender):

            mock_user_repo.get_user_by_email.return_value = {
                "id": 1,
                "email": "test@example.com",
                "is_verified": False,
                "language": "en"
            }
            mock_user_repo.save_verification_code.return_value = True

            resend_data = ResendVerificationRequest(email="test@example.com")
            response = client.post("/api/v1/auth/resend-verification", json=resend_data.model_dump())

            assert response.status_code == 200
            assert response.json()["message"] == "Verification code sent"
            mock_email_sender.assert_called_once()

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(self, client, mock_user_repo):
        """Test resend verification for already verified user"""
        with patch('apps.api.routers.auth.get_service', return_value=mock_user_repo):
            mock_user_repo.get_user_by_email.return_value = {
                "id": 1,
                "email": "test@example.com",
                "is_verified": True
            }

            resend_data = ResendVerificationRequest(email="test@example.com")
            response = client.post("/api/v1/auth/resend-verification", json=resend_data.model_dump())

            assert response.status_code == 400
            assert "User already verified" in response.json()["detail"]