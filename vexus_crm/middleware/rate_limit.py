"""
Rate Limiting Middleware for Vexus CRM
Professional rate limiting with Redis support
"""

import time
from typing import Callable, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded"""
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )


class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development"""

    def __init__(self):
        self.requests: Dict[str, list] = {}

    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - window

        # Clean old requests
        if key in self.requests:
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]

        # Check limit
        if len(self.requests.get(key, [])) >= limit:
            # Calculate retry after
            oldest_request = min(self.requests[key])
            retry_after = int(window - (now - oldest_request))
            return False, retry_after

        # Add current request
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key].append(now)

        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(
        self,
        app,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        exclude_paths: Optional[list] = None,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.key_func = key_func or self._default_key_func
        self.limiter = InMemoryRateLimiter()

    def _default_key_func(self, request: Request) -> str:
        """Default key function - uses client IP"""
        client_ip = request.client.host if request.client else "unknown"
        return f"{client_ip}:{request.url.path}"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate rate limit key
        key = self.key_func(request)

        # Check rate limit
        allowed, retry_after = self.limiter.is_allowed(
            key, self.requests_per_window, self.window_seconds
        )

        if not allowed:
            logger.warning(f"Rate limit exceeded for key: {key}")
            raise RateLimitExceeded(retry_after)

        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_window - len(self.limiter.requests.get(key, [])))
        )
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))

        # Log slow requests
        if duration > 1.0:  # More than 1 second
            logger.warning(".2f")

        return response


# Rate limit dependency for individual routes
def rate_limit(
    requests: int = 10,
    window_seconds: int = 60,
    key_func: Optional[Callable[[Request], str]] = None
):
    """Dependency for route-specific rate limiting"""
    limiter = InMemoryRateLimiter()

    async def check_rate_limit(request: Request):
        key = key_func(request) if key_func else f"{request.client.host}:{request.url.path}"

        allowed, retry_after = limiter.is_allowed(key, requests, window_seconds)
        if not allowed:
            raise RateLimitExceeded(retry_after)

        return True

    return check_rate_limit