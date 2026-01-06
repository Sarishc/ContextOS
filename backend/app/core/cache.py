"""Query caching system."""
import hashlib
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from cachetools import TTLCache
from app.core.logging import get_logger

logger = get_logger(__name__)


class QueryCache:
    """Cache for repeated queries."""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600
    ) -> None:
        """
        Initialize query cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time to live in seconds
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0
        }
        logger.info(f"QueryCache initialized: max_size={max_size}, ttl={ttl_seconds}s")
    
    def _generate_key(self, query: str, **kwargs) -> str:
        """
        Generate cache key from query and parameters.
        
        Args:
            query: Query string
            **kwargs: Additional parameters
            
        Returns:
            Cache key (hash)
        """
        # Create deterministic key from query and params
        key_data = {
            'query': query.strip().lower(),
            **{k: v for k, v in sorted(kwargs.items())}
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, query: str, **kwargs) -> Optional[Any]:
        """
        Get cached result.
        
        Args:
            query: Query string
            **kwargs: Additional parameters
            
        Returns:
            Cached result or None
        """
        key = self._generate_key(query, **kwargs)
        
        if key in self.cache:
            self.stats['hits'] += 1
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return self.cache[key]
        
        self.stats['misses'] += 1
        logger.debug(f"Cache miss for query: {query[:50]}...")
        return None
    
    def set(self, query: str, result: Any, **kwargs) -> None:
        """
        Cache a result.
        
        Args:
            query: Query string
            result: Result to cache
            **kwargs: Additional parameters
        """
        key = self._generate_key(query, **kwargs)
        self.cache[key] = result
        self.stats['sets'] += 1
        logger.debug(f"Cached result for query: {query[:50]}...")
    
    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (
            (self.stats['hits'] / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        return {
            'size': len(self.cache),
            'max_size': self.cache.maxsize,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }


# Global cache instance
query_cache = QueryCache(max_size=1000, ttl_seconds=3600)  # 1 hour TTL

