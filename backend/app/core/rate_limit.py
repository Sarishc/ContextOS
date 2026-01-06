"""Rate limiting system."""
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://"
)


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key from request.
    
    Can be customized to use user ID, API key, etc.
    """
    # For now, use IP address
    # In production, you might want to use user ID or API key
    return get_remote_address(request)


async def check_rate_limit(
    request: Request,
    limit: str = "100/minute"
) -> None:
    """
    Check rate limit for request.
    
    Args:
        request: FastAPI request
        limit: Rate limit string (e.g., "100/minute")
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    # This is handled by slowapi middleware
    # This function is for manual checks if needed
    pass

