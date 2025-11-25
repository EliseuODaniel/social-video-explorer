"""
Video providers package

This package contains implementations of video content providers for various
social media platforms, including rate limiting, caching, and circuit breaker
functionality for production resilience.
"""

from .base import BaseVideoProvider
from .meta import MetaProvider
from .mock import MockMetaProvider
from .rate_limiter import RateLimiter, get_rate_limiter
from .cache import LRUCache, get_cache, CacheManager
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    get_circuit_breaker,
    circuit_breaker,
    async_circuit_breaker
)

__all__ = [
    "BaseVideoProvider",
    "MetaProvider",
    "MockMetaProvider",
    "RateLimiter",
    "get_rate_limiter",
    "LRUCache",
    "get_cache",
    "CacheManager",
    "CircuitBreaker",
    "CircuitBreakerManager",
    "get_circuit_breaker",
    "circuit_breaker",
    "async_circuit_breaker",
]
