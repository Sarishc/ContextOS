"""Redis service for caching."""
import json
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import CacheException

logger = get_logger(__name__)


class RedisService:
    """Redis service for caching operations."""
    
    def __init__(self) -> None:
        """Initialize Redis service."""
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheException(f"Redis connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            raise CacheException("Redis client not initialized")
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting key '{key}' from cache: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            raise CacheException("Redis client not initialized")
        
        try:
            serialized = json.dumps(value)
            if expire:
                await self.redis_client.setex(key, expire, serialized)
            else:
                await self.redis_client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting key '{key}' in cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            raise CacheException("Redis client not initialized")
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key '{key}' from cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            raise CacheException("Redis client not initialized")
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking key '{key}' existence: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.redis_client:
            raise CacheException("Redis client not initialized")
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern '{pattern}': {e}")
            return 0


# Global Redis service instance
redis_service = RedisService()


async def get_redis() -> RedisService:
    """Get Redis service dependency."""
    return redis_service

