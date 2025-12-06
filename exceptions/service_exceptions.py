# exceptions/service_exceptions.py - Service-related exceptions
from typing import Optional, Dict, Any
from .base_exceptions import FireFeedException


class DuplicateDetectionException(FireFeedException):
    """Exception raised when duplicate detection fails"""

    def __init__(self, error: str, details: Optional[Dict[str, Any]] = None):
        message = f"Duplicate detection failed: {error}"
        super().__init__(message, details)
        self.error = error


class ConfigurationException(FireFeedException):
    """Exception raised when configuration is invalid"""

    def __init__(self, config_key: str, error: str, details: Optional[Dict[str, Any]] = None):
        message = f"Configuration error for '{config_key}': {error}"
        super().__init__(message, details)
        self.config_key = config_key
        self.error = error


class ServiceUnavailableException(FireFeedException):
    """Exception raised when a service is unavailable"""

    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Service '{service_name}' is unavailable"
        super().__init__(message, details)
        self.service_name = service_name