import pytest
from unittest.mock import patch, AsyncMock
from apps.api.email_service.sender import send_verification_email


@pytest.mark.asyncio
class TestEmailService:
    async def test_send_verification_email_success(self):
        """Test successful sending of verification email"""
        with patch('apps.api.email_service.sender.send_email_async', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await send_verification_email("test@example.com", "123456", "en")
            assert result is True
            mock_send.assert_called_once()

    async def test_send_verification_email_failure(self):
        """Test failure in sending verification email"""
        with patch('apps.api.email_service.sender.send_email_async', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = False

            result = await send_verification_email("test@example.com", "123456", "en")
            assert result is False
            mock_send.assert_called_once()

    async def test_send_verification_email_exception(self):
        """Test exception in sending verification email"""
        with patch('apps.api.email_service.sender.send_email_async', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP error")

            result = await send_verification_email("test@example.com", "123456", "en")
            assert result is False
            mock_send.assert_called_once()
