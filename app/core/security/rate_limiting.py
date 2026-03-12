"""
Advanced rate limiting module with DDoS protection
"""

import time
import asyncio
import json
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RateLimitAlgorithm(Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    refill_rate: float = 1.0  # tokens per second


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""

    pass


class AdvancedRateLimiter:
    """Advanced rate limiter with multiple algorithms"""

    def __init__(
        self, algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    ):
        self.algorithm = algorithm
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.buckets: Dict[str, float] = defaultdict(float)
        self.last_refill: Dict[str, float] = defaultdict(float)
        self.blocked_ips: set = set()
        self.whitelist: set = set()

    def is_allowed(self, identifier: str, config: RateLimitConfig) -> bool:
        """Check if request is allowed"""
        if identifier in self.blocked_ips:
            return False
        if identifier in self.whitelist:
            return True

        if self.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return self._check_fixed_window(identifier, config)
        elif self.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._check_sliding_window(identifier, config)
        elif self.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return self._check_token_bucket(identifier, config)
        return True

    def _check_fixed_window(self, identifier: str, config: RateLimitConfig) -> bool:
        """Fixed window rate limiting"""
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        # Remove old requests
        while self.requests[identifier] and self.requests[identifier][0] < window_start:
            self.requests[identifier].popleft()

        if len(self.requests[identifier]) >= config.requests_per_minute:
            return False

        self.requests[identifier].append(current_time)
        return True

    def _check_sliding_window(self, identifier: str, config: RateLimitConfig) -> bool:
        """Sliding window rate limiting"""
        current_time = time.time()
        window_size = 60  # 1 minute

        # Remove requests outside the sliding window
        while (
            self.requests[identifier]
            and self.requests[identifier][0] < current_time - window_size
        ):
            self.requests[identifier].popleft()

        if len(self.requests[identifier]) >= config.requests_per_minute:
            return False

        self.requests[identifier].append(current_time)
        return True

    def _check_token_bucket(self, identifier: str, config: RateLimitConfig) -> bool:
        """Token bucket algorithm"""
        current_time = time.time()
        time_passed = current_time - self.last_refill.get(identifier, current_time)

        # Refill tokens
        tokens_to_add = time_passed * config.refill_rate
        self.buckets[identifier] = min(
            config.burst_limit, self.buckets[identifier] + tokens_to_add
        )
        self.last_refill[identifier] = current_time

        if self.buckets[identifier] < 1:
            return False

        self.buckets[identifier] -= 1
        return True

    def block_ip(self, ip: str):
        """Block an IP address"""
        self.blocked_ips.add(ip)

    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)

    def whitelist_ip(self, ip: str):
        """Add IP to whitelist"""
        self.whitelist.add(ip)

    def get_metrics(self, identifier: str) -> Dict:
        """Get rate limiting metrics for an identifier"""
        return {
            "requests_in_window": len(self.requests[identifier]),
            "tokens_available": self.buckets.get(identifier, 0),
            "is_blocked": identifier in self.blocked_ips,
            "is_whitelisted": identifier in self.whitelist,
        }


class DDoSProtection:
    """DDoS protection layer"""

    def __init__(self, threshold: int = 1000):
        self.threshold = threshold
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.last_reset = time.time()

    def detect_ddos(self, ip: str) -> bool:
        """Detect potential DDoS from IP"""
        current_time = time.time()
        if current_time - self.last_reset > 60:  # Reset every minute
            self.request_counts.clear()
            self.last_reset = current_time

        self.request_counts[ip] += 1
        return self.request_counts[ip] > self.threshold


# Global instances
rate_limiter = AdvancedRateLimiter()
ddos_protection = DDoSProtection()


def rate_limit(identifier: str, config: Optional[RateLimitConfig] = None) -> bool:
    """Decorator for rate limiting"""
    if config is None:
        from .config import security_config

        config = RateLimitConfig(
            requests_per_minute=security_config.RATE_LIMIT_REQUESTS_PER_MINUTE,
            requests_per_hour=security_config.RATE_LIMIT_REQUESTS_PER_HOUR,
            requests_per_day=security_config.RATE_LIMIT_REQUESTS_PER_DAY,
        )

    return rate_limiter.is_allowed(identifier, config)


async def init_rate_limiter():
    """Initialize rate limiter (async startup)"""
    # Initialize any async components if needed
    pass


# Middleware for FastAPI/Starlette
class RateLimitMiddleware:
    """Rate limiting middleware"""

    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        self.app = app
        self.config = config or RateLimitConfig()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = self._get_client_ip(scope)
        if ddos_protection.detect_ddos(client_ip):
            rate_limiter.block_ip(client_ip)
            await self._send_error(send, 429, "Too Many Requests - DDoS Protection")
            return

        if not rate_limiter.is_allowed(client_ip, self.config):
            await self._send_error(send, 429, "Too Many Requests")
            return

        await self.app(scope, receive, send)

    def _get_client_ip(self, scope) -> str:
        """Extract client IP from ASGI scope"""
        headers = dict(scope.get("headers", []))
        x_forwarded_for = headers.get(b"x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.decode().split(",")[0].strip()
        return scope.get("client", ["unknown"])[0]

    async def _send_error(self, send, status: int, message: str):
        """Send error response"""
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [[b"content-type", b"application/json"]],
            }
        )
