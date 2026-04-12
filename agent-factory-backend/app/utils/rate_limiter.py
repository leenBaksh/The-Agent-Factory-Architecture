"""
Rate limiting utilities for API endpoints.
"""

import time
from typing import Dict, Optional
from collections import defaultdict

from fastapi import Request, HTTPException, status


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        block_duration_seconds: int = 300
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
            block_duration_seconds: How long to block after exceeding limit
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration_seconds = block_duration_seconds
        
        # Track requests: {identifier: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
        # Track blocked: {identifier: blocked_until}
        self.blocked: Dict[str, float] = {}

    def is_rate_limited(self, identifier: str) -> tuple[bool, Optional[int]]:
        """
        Check if identifier is rate limited.
        
        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        now = time.time()
        
        # Check if currently blocked
        if identifier in self.blocked:
            if now < self.blocked[identifier]:
                retry_after = int(self.blocked[identifier] - now)
                return True, retry_after
            else:
                # Block expired, remove it
                del self.blocked[identifier]
                self.requests[identifier] = []

        # Clean old requests outside the window
        cutoff = now - self.window_seconds
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]

        # Check if exceeded limit
        if len(self.requests[identifier]) >= self.max_requests:
            # Block the user
            self.blocked[identifier] = now + self.block_duration_seconds
            return True, self.block_duration_seconds

        # Record this request
        self.requests[identifier].append(now)
        return False, None

    def reset(self, identifier: str):
        """Reset rate limit for an identifier."""
        if identifier in self.requests:
            del self.requests[identifier]
        if identifier in self.blocked:
            del self.blocked[identifier]


# Global rate limiters
login_rate_limiter = RateLimiter(
    max_requests=5,  # 5 login attempts
    window_seconds=300,  # per 5 minutes
    block_duration_seconds=900  # block for 15 minutes
)

password_reset_rate_limiter = RateLimiter(
    max_requests=3,  # 3 reset attempts
    window_seconds=3600,  # per hour
    block_duration_seconds=3600  # block for 1 hour
)

verify_2fa_rate_limiter = RateLimiter(
    max_requests=5,  # 5 verification attempts
    window_seconds=300,  # per 5 minutes
    block_duration_seconds=600  # block for 10 minutes
)


def check_rate_limit(limiter: RateLimiter, identifier: str) -> Optional[int]:
    """
    Check rate limit and raise HTTPException if exceeded.
    
    Returns:
        Retry-After seconds if not limited, raises exception if limited
    """
    is_limited, retry_after = limiter.is_rate_limited(identifier)
    
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many attempts. Please try again later.",
                "retry_after": retry_after
            }
        )
    
    return retry_after
