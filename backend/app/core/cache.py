"""
Konfiguracja cache - fastapi-cache2 z InMemoryBackend lub Redis
"""
import logging
from typing import Optional

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

logger = logging.getLogger(__name__)


def init_cache(redis_url: Optional[str] = None):
    """
    Inicjalizuje FastAPI Cache

    Args:
        redis_url: URL do Redis (opcjonalnie). Jeśli None, użyje InMemoryBackend
    """
    if redis_url:
        try:
            from fastapi_cache.backends.redis import RedisBackend
            from redis import asyncio as aioredis

            redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
            FastAPICache.init(RedisBackend(redis), prefix="tamteklipy-cache:")
            logger.info(f"Cache initialized with Redis backend: {redis_url}")
        except ImportError:
            logger.warning("Redis not available, falling back to InMemoryBackend")
            FastAPICache.init(InMemoryBackend(), prefix="tamteklipy-cache:")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}, using InMemoryBackend")
            FastAPICache.init(InMemoryBackend(), prefix="tamteklipy-cache:")
    else:
        FastAPICache.init(InMemoryBackend(), prefix="tamteklipy-cache:")
        logger.info("Cache initialized with InMemoryBackend")


async def invalidate_cache(pattern: str):
    """
    Invaliduje cache pasujący do wzorca
    """
    try:
        backend = FastAPICache.get_backend()
        logger.debug(f"🔍 Attempting to invalidate cache pattern: {pattern}")
        logger.debug(f"📦 Backend type: {type(backend).__name__}")

        if hasattr(backend, 'clear'):
            # InMemoryBackend ma metodę clear
            await backend.clear()
            logger.info(f"✅ Cache cleared (pattern: {pattern})")
        else:
            # Redis backend - można użyć scan
            logger.warning("❌ Cache invalidation not fully supported for this backend")
            # Dla Redis dodaj konkretną implementację
            if hasattr(backend, 'redis'):
                keys = await backend.redis.keys(f"*{pattern}*")
                if keys:
                    await backend.redis.delete(*keys)
                    logger.info(f"✅ Redis cache cleared: {len(keys)} keys matching {pattern}")
    except Exception as e:
        logger.error(f"❌ Failed to invalidate cache: {e}")


def cache_key_builder(
        func,
        namespace: str = "",
        request=None,
        response=None,
        args=None,
        kwargs=None,
):
    """
    Custom cache key builder uwzględniający query params
    """
    from fastapi_cache import FastAPICache

    prefix = FastAPICache.get_prefix()
    cache_key = f"{prefix}:{namespace}"

    # Dodaj query params do klucza
    if request:
        query_params = dict(request.query_params)
        if query_params:
            # Sortuj parametry dla konsystentności
            sorted_params = sorted(query_params.items())
            params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            cache_key += f":{params_str}"

    # DEBUG: Loguj generowany klucz
    logger.debug(f"🔄 Generated cache key: {cache_key} for {namespace}")
    logger.debug(f"📋 Query params: {dict(request.query_params) if request else 'No request'}")

    return cache_key