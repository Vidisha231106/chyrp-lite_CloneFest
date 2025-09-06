# cache.py

import os
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import redis

def setup_cache():
    """Setup Redis cache for the application."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Create Redis connection
    redis_client = redis.from_url(redis_url, encoding="utf8", decode_responses=True)
    
    # Initialize FastAPI cache with Redis backend
    FastAPICache.init(RedisBackend(redis_client), prefix="chyrp-cache")

# Cache decorators for different timeouts
def cache_for_5_minutes():
    """Cache for 5 minutes."""
    return cache(expire=300)

def cache_for_1_hour():
    """Cache for 1 hour."""
    return cache(expire=3600)

def cache_for_1_day():
    """Cache for 1 day."""
    return cache(expire=86400)

def cache_for_1_week():
    """Cache for 1 week."""
    return cache(expire=604800)
