import pytest
from unittest.mock import patch, AsyncMock
from services.email_service.sender import send_registration_success_email


@pytest.mark.asyncio
class TestRegistrationSuccessEmail:
    async def test_send_registration_success_email_success(self):
        """Test successful sending of registration success email"""
        with patch('services.email_service.sender.get_service', return_value={'SMTP_SERVER': 'localhost', 'SMTP_PORT': 587, 'SMTP_USERNAME': '', 'SMTP_PASSWORD': '', 'FROM_EMAIL': 'test@example.com'}):
            with patch('services.email_service.sender.send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = None

                result = await send_registration_success_email("test@example.com", "en")
                assert result is True
                mock_send.assert_called_once()

    async def test_send_registration_success_email_failure(self):
        """Test failure in sending registration success email"""
        with patch('services.email_service.sender.get_service', return_value={'SMTP_SERVER': 'localhost', 'SMTP_PORT': 587, 'SMTP_USERNAME': '', 'SMTP_PASSWORD': '', 'FROM_EMAIL': 'test@example.com'}):
            with patch('services.email_service.sender.send', new_callable=AsyncMock) as mock_send:
                mock_send.side_effect = Exception("SMTP error")

                result = await send_registration_success_email("test@example.com", "en")
                assert result is False
                mock_send.assert_called_once()

    async def test_send_registration_success_email_exception(self):
        """Test exception in sending registration success email"""
        with patch('services.email_service.sender.get_service', return_value={'SMTP_SERVER': 'localhost', 'SMTP_PORT': 587, 'SMTP_USERNAME': '', 'SMTP_PASSWORD': '', 'FROM_EMAIL': 'test@example.com'}):
            with patch('services.email_service.sender.send', new_callable=AsyncMock) as mock_send:
                mock_send.side_effect = Exception("SMTP error")

                result = await send_registration_success_email("test@example.com", "en")
                assert result is False
                mock_send.assert_called_once()