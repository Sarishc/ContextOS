"""Custom exceptions."""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize exception."""
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(AppException):
    """Database-related exception."""
    
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize database exception."""
        super().__init__(message, status_code=500, details=details)


class CacheException(AppException):
    """Cache-related exception."""
    
    def __init__(self, message: str = "Cache error", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize cache exception."""
        super().__init__(message, status_code=500, details=details)


class ValidationException(AppException):
    """Validation exception."""
    
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize validation exception."""
        super().__init__(message, status_code=422, details=details)


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize not found exception."""
        super().__init__(message, status_code=404, details=details)

