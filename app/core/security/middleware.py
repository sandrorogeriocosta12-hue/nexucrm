    """
    Unified security middleware for FastAPI/Starlette applications
    """
    import json
    from typing import Optional
    from fastapi import Request, Response
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    from .config import security_config
    from .rate_limiting import RateLimitMiddleware, RateLimitConfig, rate_limiter, ddos_protection
    from .logging import SecurityLoggingMiddleware, log_rate_limit_exceeded, log_attack_attempt, SecurityEventType
    from .validation import InputValidator

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""

async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

# Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = security_config.X_FRAME_OPTIONS
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = f"max-age={security_config.HSTS_MAX_AGE}"
        response.headers["Content-Security-Policy"] = security_config.CSP_POLICY
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation on requests"""

async def dispatch(self, request: Request, call_next):
# Validate query parameters
        for key, value in request.query_params.items():
            if isinstance(value, str):
                if InputValidator.detect_sql_injection(value):
                    log_attack_attempt(
                        SecurityEventType.SQL_INJECTION_ATTEMPT,
                        self._get_client_ip(request),
                        value,
                        str(request.url),
                        getattr(request.state, 'user_id', None)
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid input detected"}
                    )
                if InputValidator.detect_xss(value):
                    log_attack_attempt(
                        SecurityEventType.XSS_ATTEMPT,
                        self._get_client_ip(request),
                        value,
                        str(request.url),
                        getattr(request.state, 'user_id', None)
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid input detected"}
                    )

# For POST/PUT/PATCH, validate JSON body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode()
                    if InputValidator.detect_sql_injection(body_str):
                        log_attack_attempt(
                            SecurityEventType.SQL_INJECTION_ATTEMPT,
                            self._get_client_ip(request),
                            body_str[:100],  # Log first 100 chars
                            str(request.url),
                            getattr(request.state, 'user_id', None)
                        )
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Invalid input detected"}
                        )
            except:
                pass

        response = await call_next(request)
        return response

def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class SecurityMiddleware:
    """Unified security middleware combining all security features"""

def __init__(self, app):
        self.app = app

async def __call__(self, scope, receive, send):
# Apply rate limiting first
        rate_config = RateLimitConfig(
            requests_per_minute=security_config.RATE_LIMIT_REQUESTS_PER_MINUTE,
            requests_per_hour=security_config.RATE_LIMIT_REQUESTS_PER_HOUR,
            requests_per_day=security_config.RATE_LIMIT_REQUESTS_PER_DAY
        )

# Check DDoS protection
        if scope["type"] == "http":
            client_ip = self._get_client_ip(scope)
            if ddos_protection.detect_ddos(client_ip):
                rate_limiter.block_ip(client_ip)
                await self._send_error(send, 429, "Too Many Requests - DDoS Protection")
                return

# Check rate limit
            if not rate_limiter.is_allowed(client_ip, rate_config):
                log_rate_limit_exceeded(client_ip, scope.get("path", ""), 0)
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
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                [b"content-type", b"application/json"],
                [b"x-content-type-options", b"nosniff"],
                [b"x-frame-options", b"DENY"],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps({"error": message}).encode(),
        })

def setup_security_middleware(app):
    """Setup all security middleware for a FastAPI app"""

# Add security middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(SecurityLoggingMiddleware)

# Add rate limiting middleware
    rate_config = RateLimitConfig(
        requests_per_minute=security_config.RATE_LIMIT_REQUESTS_PER_MINUTE,
        requests_per_hour=security_config.RATE_LIMIT_REQUESTS_PER_HOUR,
        requests_per_day=security_config.RATE_LIMIT_REQUESTS_PER_DAY
    )
    app.add_middleware(RateLimitMiddleware, config=rate_config)

    return app