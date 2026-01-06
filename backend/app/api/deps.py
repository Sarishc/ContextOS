"""API dependencies."""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.redis_service import RedisService, get_redis


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db():
        yield session


async def get_redis_service() -> RedisService:
    """Get Redis service dependency."""
    return await get_redis()

