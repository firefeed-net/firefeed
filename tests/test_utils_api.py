import pytest
import httpx
from typing import List, Dict, Any
from pydantic import BaseModel
from unittest.mock import patch, MagicMock, AsyncMock
from utils.api import APIResponse, PaginatedResponse, make_request
from tests.test_utils_async_mocks import create_httpx_client_mock


class TestAPIResponse:
    """Test the APIResponse utility class"""
    
    def test_paginated_response(self):
        """Test paginated response formatting"""
        count = 10
        results = [{"id": 1, "name": "test"}]
        
        response = APIResponse.paginated_response(count, results)
        
        assert response == {"count": 10, "results": [{"id": 1, "name": "test"}]}
    
    def test_single_item_response(self):
        """Test single item response formatting"""
        item = {"id": 1, "name": "test"}
        
        response = APIResponse.single_item_response(item)
        
        assert response == {"result": {"id": 1, "name": "test"}}
    
    def test_success_response_default(self):
        """Test success response with default message"""
        response = APIResponse.success_response()
        
        assert response == {"message": "Success"}
    
    def test_success_response_custom(self):
        """Test success response with custom message"""
        message = "Operation completed successfully"
        response = APIResponse.success_response(message)
        
        assert response == {"message": "Operation completed successfully"}
    
    def test_error_response_default_status(self):
        """Test error response with default status code"""
        message = "Something went wrong"
        response = APIResponse.error_response(message)
        
        assert response == {"error": "Something went wrong", "status_code": 400}
    
    def test_error_response_custom_status(self):
        """Test error response with custom status code"""
        message = "Not found"
        status_code = 404
        response = APIResponse.error_response(message, status_code)
        
        assert response == {"error": "Not found", "status_code": 404}


class TestPaginatedResponse:
    """Test the PaginatedResponse model"""
    
    def test_paginated_response_model(self):
        """Test PaginatedResponse model creation"""
        class TestItem(BaseModel):
            id: int
            name: str
        
        count = 5
        results = [TestItem(id=1, name="test1"), TestItem(id=2, name="test2")]
        
        paginated_response = PaginatedResponse[TestItem](count=count, results=results)
        
        assert paginated_response.count == 5
        assert len(paginated_response.results) == 2
        assert paginated_response.results[0].id == 1
        assert paginated_response.results[0].name == "test1"
        assert paginated_response.results[1].id == 2
        assert paginated_response.results[1].name == "test2"


class TestMakeRequest:
    """Test the make_request function"""
    
    def test_make_request_success(self):
        """Test successful HTTP request"""
        mock_client, mock_response = create_httpx_client_mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch('httpx.Client', return_value=mock_client):
            result = make_request("https://example.com")
            
            assert result == {"status_code": 200, "data": {"data": "test"}}
            mock_client.request.assert_called_once_with("GET", "https://example.com", headers=None, data=None)
    
    def test_make_request_with_method(self):
        """Test HTTP request with custom method"""
        mock_client, mock_response = create_httpx_client_mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"created": True}
        
        with patch('httpx.Client', return_value=mock_client):
            result = make_request("https://example.com", method="POST", data='{"test": "data"}')
            
            assert result == {"status_code": 201, "data": {"created": True}}
            mock_client.request.assert_called_once_with("POST", "https://example.com", headers=None, data='{"test": "data"}')
    
    def test_make_request_with_headers(self):
        """Test HTTP request with custom headers"""
        mock_client, mock_response = create_httpx_client_mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch('httpx.Client', return_value=mock_client):
            headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
            result = make_request("https://example.com", headers=headers)
            
            assert result == {"status_code": 200, "data": {"data": "test"}}
            mock_client.request.assert_called_once_with("GET", "https://example.com", headers=headers, data=None)
    
    def test_make_request_with_timeout(self):
        """Test HTTP request with timeout"""
        mock_client, mock_response = create_httpx_client_mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch('httpx.Client', return_value=mock_client):
            result = make_request("https://example.com", timeout=30.0)
            
            assert result == {"status_code": 200, "data": {"data": "test"}}
            mock_client.request.assert_called_once_with("GET", "https://example.com", headers=None, data=None)
    
    def test_make_request_http_error(self):
        """Test HTTP request with HTTP error"""
        mock_client, mock_response = create_httpx_client_mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        
        # Mock the request to raise HTTPStatusError
        def mock_request(*args, **kwargs):
            raise httpx.HTTPStatusError(
                message="Not Found",
                request=MagicMock(),
                response=mock_response
            )
        
        mock_client.request = mock_request
        
        with patch('httpx.Client', return_value=mock_client):
            result = make_request("https://example.com")
            
            assert result == {"status_code": 404, "error": "Not Found"}
    
    def test_make_request_general_exception(self):
        """Test HTTP request with general exception"""
        mock_client, mock_response = create_httpx_client_mock()
        
        # Mock the request to raise general exception
        def mock_request(*args, **kwargs):
            raise Exception("Connection failed")
        
        mock_client.request = mock_request
        
        with patch('httpx.Client', return_value=mock_client):
            result = make_request("https://example.com")
            
            assert result == {"status_code": 500, "error": "Connection failed"}