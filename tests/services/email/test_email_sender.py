import pytest
from unittest.mock import patch, AsyncMock
from services.email_service.sender import EmailSender


@pytest.fixture
def email_sender():
    return EmailSender()


class TestEmailSender:
    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, email_sender):
        with patch('services.email_service.sender.get_service') as mock_get_service, \
             patch('services.email_service.sender.send') as mock_send:

            mock_config = {
                'SMTP_SERVER': 'smtp.example.com',
                'SMTP_PORT': 587,
                'SMTP_EMAIL': 'test@example.com',
                'SMTP_PASSWORD': 'password',
                'SMTP_USE_TLS': 'true'
            }
            mock_get_service.return_value = mock_config

            mock_send.return_value = None  # Success

            result = await email_sender.send_verification_email("user@example.com", "123456", "en")

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_email_failure(self, email_sender):
        with patch('services.email_service.sender.get_service') as mock_get_service, \
             patch('services.email_service.sender.send') as mock_send:

            mock_config = {
                'SMTP_SERVER': 'smtp.example.com',
                'SMTP_PORT': 587,
                'SMTP_EMAIL': 'test@example.com',
                'SMTP_PASSWORD': 'password',
                'SMTP_USE_TLS': 'true'
            }
            mock_get_service.return_value = mock_config

            mock_send.side_effect = Exception("SMTP error")

            result = await email_sender.send_verification_email("user@example.com", "123456", "en")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(self, email_sender):
        with patch('services.email_service.sender.get_service') as mock_get_service, \
             patch('services.email_service.sender.send') as mock_send:

            mock_config = {
                'SMTP_SERVER': 'smtp.example.com',
                'SMTP_PORT': 465,
                'SMTP_EMAIL': 'test@example.com',
                'SMTP_PASSWORD': 'password',
                'SMTP_USE_TLS': 'false'
            }
            mock_get_service.return_value = mock_config

            mock_send.return_value = None

            result = await email_sender.send_password_reset_email("user@example.com", "reset_token", "en")

            assert result is True

    @pytest.mark.asyncio
    async def test_send_registration_success_email_success(self, email_sender):
        with patch('services.email_service.sender.get_service') as mock_get_service, \
             patch('services.email_service.sender.send') as mock_send:

            mock_config = {
                'SMTP_SERVER': 'smtp.example.com',
                'SMTP_PORT': 465,
                'SMTP_EMAIL': 'test@example.com',
                'SMTP_PASSWORD': 'password',
                'SMTP_USE_TLS': 'false'
            }
            mock_get_service.return_value = mock_config

            mock_send.return_value = None

            result = await email_sender.send_registration_success_email("user@example.com", "en")

            assert result is True

    def test_get_subject(self, email_sender):
        assert email_sender._get_subject("en") == "FireFeed - Account Verification Code"
        assert email_sender._get_subject("ru") == "FireFeed - Код подтверждения аккаунта"
        assert email_sender._get_subject("de") == "FireFeed - Konto-Verifizierungscode"
        assert email_sender._get_subject("unknown") == "FireFeed - Account Verification Code"

    def test_get_reset_subject(self, email_sender):
        assert email_sender._get_reset_subject("en") == "FireFeed - Password Reset"
        assert email_sender._get_reset_subject("ru") == "FireFeed - Сброс пароля"
        assert email_sender._get_reset_subject("de") == "FireFeed - Passwort zurücksetzen"
        assert email_sender._get_reset_subject("unknown") == "FireFeed - Password Reset"