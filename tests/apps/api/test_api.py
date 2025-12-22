import pytest
from unittest.mock import patch, MagicMock
import httpx
from utils.api import make_request

class TestMakeRequest:
    @patch('utils.api.httpx.Client')
    def test_make_request_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = make_request("http://example.com")

        assert result == {"status_code": 200, "data": {"key": "value"}}
        mock_client.request.assert_called_once_with("GET", "http://example.com", headers=None, data=None)

    @patch('utils.api.httpx.Client')
    def test_make_request_with_params(self, mock_client_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"created": True}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = make_request("http://example.com", method="POST", headers={"Content-Type": "application/json"}, data='{"test": "data"}', timeout=5)

        assert result == {"status_code": 201, "data": {"created": True}}
        mock_client.request.assert_called_once_with("POST", "http://example.com", headers={"Content-Type": "application/json"}, data='{"test": "data"}')
        mock_client_class.assert_called_once_with(timeout=5)

    @patch('utils.api.httpx.Client')
    def test_make_request_http_error(self, mock_client_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        mock_client.request.return_value.raise_for_status.side_effect = http_error
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = make_request("http://example.com")

        assert result == {"status_code": 404, "error": "Not Found"}

    @patch('utils.api.httpx.Client')
    def test_make_request_general_exception(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.request.side_effect = Exception("Network error")
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = make_request("http://example.com")

        assert result == {"status_code": 500, "error": "Network error"}