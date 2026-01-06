"""Health check endpoints."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_redis_service
from app.services.redis_service import RedisService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@router.get("/health/ready", response_model=Dict[str, Any])
async def readiness_check(
    db: AsyncSession = Depends(get_db_session),
    redis: RedisService = Depends(get_redis_service),
) -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Checks if the application is ready to serve requests.
    """
    checks = {
        "database": "unknown",
        "redis": "unknown",
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        await result.scalar()
        checks["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = "unhealthy"
    
    # Check Redis
    try:
        await redis.redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        checks["redis"] = "unhealthy"
    
    all_healthy = all(status == "healthy" for status in checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "app": settings.APP_NAME,
    }


@router.get("/health/live", response_model=Dict[str, Any])
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.
    Checks if the application is alive and running.
    """
    return {
        "status": "alive",
        "app": settings.APP_NAME,
    }

