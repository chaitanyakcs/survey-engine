"""
Cache service for Redis operations
"""
import redis
from typing import Optional, Any
from src.config.settings import settings


class CacheService:
    """Redis cache service"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            # Test connection
            self.redis_client.ping()
        except Exception:
            # Redis not available - use in-memory fallback
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get(key)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.set(key, value, ex=expire)
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False


# Global cache service instance
cache_service = CacheService()
redis_client = cache_service.redis_client
