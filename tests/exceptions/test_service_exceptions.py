import pytest
from exceptions.base_exceptions import FireFeedException
from exceptions.service_exceptions import DuplicateDetectionException, ConfigurationException, ServiceUnavailableException


class TestDuplicateDetectionException:
    """Test the DuplicateDetectionException"""
    
    def test_duplicate_detection_exception_no_details(self):
        """Test DuplicateDetectionException with no details"""
        error = "Vector embedding failed"
        exception = DuplicateDetectionException(error)
        
        assert str(exception) == "Duplicate detection failed: Vector embedding failed"
        assert exception.message == "Duplicate detection failed: Vector embedding failed"
        assert exception.error == "Vector embedding failed"
        assert exception.details == {}
    
    def test_duplicate_detection_exception_with_details(self):
        """Test DuplicateDetectionException with details"""
        error = "Database connection timeout"
        details = {"operation": "check_duplicate", "item_id": 123}
        exception = DuplicateDetectionException(error, details)
        
        assert str(exception) == "Duplicate detection failed: Database connection timeout"
        assert exception.message == "Duplicate detection failed: Database connection timeout"
        assert exception.error == "Database connection timeout"
        assert exception.details == {"operation": "check_duplicate", "item_id": 123}
    
    def test_duplicate_detection_exception_inheritance(self):
        """Test that DuplicateDetectionException inherits from FireFeedException"""
        error = "Test error"
        exception = DuplicateDetectionException(error)
        
        assert isinstance(exception, FireFeedException)
        assert isinstance(exception, Exception)


class TestConfigurationException:
    """Test the ConfigurationException"""
    
    def test_configuration_exception_no_details(self):
        """Test ConfigurationException with no details"""
        config_key = "database_url"
        error = "Invalid URL format"
        exception = ConfigurationException(config_key, error)
        
        assert str(exception) == "Configuration error for 'database_url': Invalid URL format"
        assert exception.message == "Configuration error for 'database_url': Invalid URL format"
        assert exception.config_key == "database_url"
        assert exception.error == "Invalid URL format"
        assert exception.details == {}
    
    def test_configuration_exception_with_details(self):
        """Test ConfigurationException with details"""
        config_key = "redis_host"
        error = "Host not reachable"
        details = {"host": "localhost", "port": 6379}
        exception = ConfigurationException(config_key, error, details)
        
        assert str(exception) == "Configuration error for 'redis_host': Host not reachable"
        assert exception.message == "Configuration error for 'redis_host': Host not reachable"
        assert exception.config_key == "redis_host"
        assert exception.error == "Host not reachable"
        assert exception.details == {"host": "localhost", "port": 6379}
    
    def test_configuration_exception_inheritance(self):
        """Test that ConfigurationException inherits from FireFeedException"""
        config_key = "test_key"
        error = "Test error"
        exception = ConfigurationException(config_key, error)
        
        assert isinstance(exception, FireFeedException)
        assert isinstance(exception, Exception)


class TestServiceUnavailableException:
    """Test the ServiceUnavailableException"""
    
    def test_service_unavailable_exception_no_details(self):
        """Test ServiceUnavailableException with no details"""
        service_name = "translation_service"
        exception = ServiceUnavailableException(service_name)
        
        assert str(exception) == "Service 'translation_service' is unavailable"
        assert exception.message == "Service 'translation_service' is unavailable"
        assert exception.service_name == "translation_service"
        assert exception.details == {}
    
    def test_service_unavailable_exception_with_details(self):
        """Test ServiceUnavailableException with details"""
        service_name = "email_service"
        details = {"error": "SMTP connection failed", "retry_after": 30}
        exception = ServiceUnavailableException(service_name, details)
        
        assert str(exception) == "Service 'email_service' is unavailable"
        assert exception.message == "Service 'email_service' is unavailable"
        assert exception.service_name == "email_service"
        assert exception.details == {"error": "SMTP connection failed", "retry_after": 30}
    
    def test_service_unavailable_exception_inheritance(self):
        """Test that ServiceUnavailableException inherits from FireFeedException"""
        service_name = "test_service"
        exception = ServiceUnavailableException(service_name)
        
        assert isinstance(exception, FireFeedException)
        assert isinstance(exception, Exception)