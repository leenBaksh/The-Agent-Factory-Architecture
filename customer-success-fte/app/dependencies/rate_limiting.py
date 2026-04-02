"""
Distributed sliding-window rate limiter with Redis backend.

Falls back to in-memory limiting if Redis is unavailable.
"""

import logging
import os
import time
from collections import defaultdict, deque
from typing import Optional, TYPE_CHECKING

from fastapi import HTTPException, Request, status

if TYPE_CHECKING:
    import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Try to import redis, but make it optional
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Using in-memory rate limiting.")


class InMemoryRateLimiter:
    """
    In-memory sliding-window rate limiter (fallback).

    Args:
        max_requests: Maximum requests allowed in the window.
        window_seconds: Duration of the sliding window in seconds.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        bucket = self._buckets[key]

        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= self.max_requests:
            return False

        bucket.append(now)
        return True

    def check(self, key: str) -> None:
        """Raise HTTP 429 if the key has exceeded its rate limit."""
        if not self.is_allowed(key):
            logger.warning("Rate limit exceeded for key: %s", key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
            )


class RedisRateLimiter:
    """
    Redis-backed distributed sliding-window rate limiter.

    Uses Redis sorted sets for efficient sliding window implementation.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int = 60,
        redis_url: Optional[str] = None,
        key_prefix: str = "ratelimit",
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        self._redis = None
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._fallback = InMemoryRateLimiter(max_requests, window_seconds)

    async def _get_redis(self):
        """Lazy-initialize Redis connection."""
        if not REDIS_AVAILABLE:
            return None
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
                logger.info("Redis rate limiter connected")
            except Exception as exc:
                logger.warning("Redis connection failed, using in-memory fallback: %s", exc)
                return None
        return self._redis

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed using Redis sorted set."""
        redis_conn = await self._get_redis()
        if redis_conn is None:
            return self._fallback.is_allowed(key)

        try:
            now = time.time()
            window_start = now - self.window_seconds
            redis_key = f"{self.key_prefix}:{key}"

            # Remove expired entries
            await redis_conn.zremrangebyscore(redis_key, 0, window_start)

            # Count current requests in window
            current_count = await redis_conn.zcard(redis_key)

            if current_count >= self.max_requests:
                return False

            # Add new request with timestamp as score
            pipe = redis_conn.pipeline()
            pipe.zadd(redis_key, {f"{now}": now})
            pipe.expire(redis_key, self.window_seconds * 2)
            await pipe.execute()

            return True

        except Exception as exc:
            logger.warning("Redis rate limit check failed, using fallback: %s", exc)
            return self._fallback.is_allowed(key)

    async def check(self, key: str) -> None:
        """Raise HTTP 429 if the key has exceeded its rate limit."""
        if not await self.is_allowed(key):
            logger.warning("Rate limit exceeded for key: %s", key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
            )


# ── Pre-built limiters per channel ────────────────────────────────────────────

_web_limiter = RedisRateLimiter(max_requests=30, window_seconds=60, key_prefix="ratelimit:web")
_gmail_limiter = RedisRateLimiter(max_requests=100, window_seconds=60, key_prefix="ratelimit:gmail")
_whatsapp_limiter = RedisRateLimiter(max_requests=100, window_seconds=60, key_prefix="ratelimit:whatsapp")


# ── Backward compatibility aliases ────────────────────────────────────────────

# Alias for backward compatibility
RateLimiter = RedisRateLimiter


def channel_rate_limit(channel: str):
    """Return the appropriate rate limiter for a channel."""
    limiters = {
        "web": _web_limiter,
        "gmail": _gmail_limiter,
        "whatsapp": _whatsapp_limiter,
    }
    return limiters.get(channel, _web_limiter)


# ── FastAPI dependency factories ───────────────────────────────────────────────

async def web_rate_limit(request: Request) -> None:
    """Dependency: rate-limit by client IP for the web form channel."""
    client_ip = request.client.host if request.client else "unknown"
    await _web_limiter.check(client_ip)


async def whatsapp_rate_limit(request: Request) -> None:
    """Dependency: rate-limit by client IP for WhatsApp webhooks."""
    client_ip = request.client.host if request.client else "unknown"
    await _whatsapp_limiter.check(client_ip)


async def gmail_rate_limit(request: Request) -> None:
    """Dependency: rate-limit by client IP for Gmail webhooks."""
    client_ip = request.client.host if request.client else "unknown"
    await _gmail_limiter.check(client_ip)
