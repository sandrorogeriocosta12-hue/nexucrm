"""
Security Middleware for Vexus CRM
Professional security headers and protection
"""

import logging
from typing import List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import time

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    def __init__(self, app, csp_directives: dict = None):
        super().__init__(app)
        self.csp_directives = csp_directives or {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            "style-src": "'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            "img-src": "'self' data: https:",
            "font-src": "'self' https://fonts.gstatic.com",
            "connect-src": "'self'",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'"
        }

    def _build_csp_header(self) -> str:
        """Build Content Security Policy header"""
        directives = []
        for directive, value in self.csp_directives.items():
            directives.append(f"{directive} {value}")
        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self._build_csp_header()

        # HSTS (HTTP Strict Transport Security) - Only in production
        if not request.url.scheme == "http":  # Only for HTTPS
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with security context"""

    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/favicon.ico"]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request
        logger.info(
            f"REQUEST: {request.method} {request.url.path} "
            f"from {client_ip} - User-Agent: {user_agent[:100]}..."
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(
                ".2f"
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"ERROR: {request.method} {request.url.path} "
                f"from {client_ip} - Duration: {duration:.2f}s - Error: {str(e)}"
            )
            raise


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Basic SQL injection protection"""

    def __init__(self, app):
        super().__init__(app)
        self.sql_keywords = [
            "union", "select", "insert", "delete", "update", "drop",
            "create", "alter", "exec", "execute", "--", "/*", "*/",
            "xp_", "sp_", "script", "javascript:", "vbscript:",
            "onload", "onerror", "alert(", "<script"
        ]

    async def dispatch(self, request: Request, call_next):
        # Check query parameters
        for key, value in request.query_params.items():
            if self._contains_suspicious_content(str(value)):
                logger.warning(f"SQL injection attempt detected in query param: {key}={value}")
                return Response(
                    content='{"error": "Bad Request"}',
                    status_code=400,
                    media_type="application/json"
                )

        # Check form data (if any)
        if hasattr(request, 'form') and request.form:
            for key, value in (await request.form()).items():
                if self._contains_suspicious_content(str(value)):
                    logger.warning(f"SQL injection attempt detected in form data: {key}")
                    return Response(
                        content='{"error": "Bad Request"}',
                        status_code=400,
                        media_type="application/json"
                    )

        return await call_next(request)

    def _contains_suspicious_content(self, content: str) -> bool:
        """Check if content contains suspicious patterns"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.sql_keywords)