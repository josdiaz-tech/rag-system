# backend/backend/app/core/rate_limiter.py
"""
Rate limiting configuration using slowapi
Prevents API abuse and controls costs
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from app.core.config import settings
from app.core.logging_config import get_security_logger
import redis
from typing import Optional

security_logger = get_security_logger()

# Redis connection for persistent rate limiting
redis_client: Optional[redis.Redis] = None

try:
    if settings.REDIS_URL:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        redis_client.ping()
        print("✅ Redis connected for rate limiting")
except Exception as e:
    print(f"⚠️  Redis not available, using in-memory rate limiting: {e}")
    redis_client = None


def is_ip_exempt(ip: str) -> bool:
    """
    Check if IP address is exempt from rate limiting
    
    Useful for:
    - Admin IP addresses
    - Monitoring services
    - Internal testing
    """
    return ip in settings.RATE_LIMIT_EXEMPT_IPS


def get_limiter_key(request: Request) -> str:
    """
    Generate unique key for rate limiting
    
    For authenticated users: Uses user email from JWT token
    For anonymous users: Uses IP address
    
    Returns None for exempt IPs (bypasses rate limiting)
    """
    # Check if IP is exempt
    client_ip = get_remote_address(request)
    if is_ip_exempt(client_ip):
        security_logger.info("Rate limit bypassed for exempt IP", extra={
            "ip": client_ip,
            "event": "rate_limit_exempt"
        })
        # Return None would disable limiting, but slowapi doesn't support that
        # So we use a special key that gets very high limits
        return f"exempt:{client_ip}"
    
    try:
        # Try to get user from JWT token
        if hasattr(request.state, "user") and request.state.user:
            user_email = request.state.user.email
            return f"user:{user_email}"
    except:
        pass
    
    # Fallback to IP address
    return f"ip:{client_ip}"


# Initialize the limiter with configurable default
limiter = Limiter(
    key_func=get_limiter_key,
    storage_uri=settings.REDIS_URL if redis_client else None,
    default_limits=[settings.RATE_LIMIT_GENERAL],  # Now configurable!
    strategy="fixed-window",
    headers_enabled=True,
    enabled=settings.RATE_LIMIT_ENABLED,  # Can be disabled via config
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom error message when rate limit is exceeded
    """
    user_identifier = get_limiter_key(request)
    
    security_logger.warning("Rate limit exceeded", extra={
        "user_identifier": user_identifier,
        "path": request.url.path,
        "method": request.method,
        "event": "rate_limit_exceeded"
    })
    
    raise HTTPException(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": "You've made too many requests. Please try again later.",
            "retry_after": exc.detail.split("Retry after ")[1] if "Retry after" in exc.detail else "1 hour",
            "limit_info": f"Current limits are configurable by system administrator",
            "contact": "If you need higher limits, please contact your system administrator"
        }
    )


# Decorator functions now use configurable limits
def get_auth_limit():
    """Get authentication rate limit from config"""
    return settings.RATE_LIMIT_AUTH


def get_upload_limit():
    """Get upload rate limit from config"""
    return settings.RATE_LIMIT_UPLOAD


def get_query_limit():
    """Get query rate limit from config"""
    return settings.RATE_LIMIT_QUERY


def get_general_limit():
    """Get general rate limit from config"""
    return settings.RATE_LIMIT_GENERAL


# Apply rate limits using config values
def apply_rate_limit(endpoint_type: str):
    """
    Apply appropriate rate limit based on endpoint type
    
    Usage:
        @apply_rate_limit("auth")
        async def login(...):
            ...
    """
    limits = {
        "auth": settings.RATE_LIMIT_AUTH,
        "upload": settings.RATE_LIMIT_UPLOAD,
        "query": settings.RATE_LIMIT_QUERY,
        "general": settings.RATE_LIMIT_GENERAL
    }
    
    limit = limits.get(endpoint_type, settings.RATE_LIMIT_GENERAL)
    return limiter.limit(limit)