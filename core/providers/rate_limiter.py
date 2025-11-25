"""
Rate limiter implementation using token bucket algorithm.

This module provides thread-safe rate limiting with configurable limits
and support for multiple rate limiters (per provider, per endpoint).
"""

import os
import time
import threading
import logging
from typing import Dict, Optional, NamedTuple
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimitStatus(NamedTuple):
    """Current status of rate limiter."""
    requests_per_hour: int
    current_requests: int
    remaining_requests: int
    time_until_reset_seconds: float
    is_limited: bool


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Refills tokens at a constant rate and allows bursts up to bucket capacity.
    Thread-safe implementation using locks.
    """

    def __init__(self, refill_rate: float, bucket_capacity: int):
        """
        Initialize token bucket.

        Args:
            refill_rate: Tokens per second (e.g., 150/3600 = 0.0417 tokens/sec)
            bucket_capacity: Maximum tokens the bucket can hold
        """
        self.refill_rate = refill_rate
        self.bucket_capacity = bucket_capacity
        self.tokens = bucket_capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if rate limited
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.bucket_capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        with self.lock:
            self._refill()

            # Calculate time until next token
            if self.tokens >= self.bucket_capacity:
                time_until_reset = 0.0
            else:
                tokens_needed = 1.0 - self.tokens
                time_until_reset = tokens_needed / self.refill_rate

            # Calculate remaining requests
            remaining_requests = max(0, int(self.tokens))
            current_requests = self.bucket_capacity - remaining_requests
            is_limited = self.tokens < 1

            return RateLimitStatus(
                requests_per_hour=self.bucket_capacity,
                current_requests=current_requests,
                remaining_requests=remaining_requests,
                time_until_reset_seconds=time_until_reset,
                is_limited=is_limited
            )


class RateLimiter:
    """
    Thread-safe rate limiter with per-provider and per-endpoint limits.

    Supports multiple rate limiters with different configurations:
    - Global app-wide rate limiting
    - Per-provider rate limiting
    - Per-endpoint specific rate limiting
    """

    def __init__(self):
        """Initialize rate limiter with configuration from environment."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

        # Load configuration from environment
        self.global_requests_per_hour = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "150"))
        self.burst_size = int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

        # Calculate refill rate (tokens per second)
        self.refill_rate = self.global_requests_per_hour / 3600.0

        # Initialize global bucket
        self.global_bucket = TokenBucket(self.refill_rate, self.burst_size)

        self._log_info(f"RateLimiter initialized: {self.global_requests_per_hour}/hour, burst: {self.burst_size}")

    def can_proceed(self, bucket_name: str = "global") -> bool:
        """
        Check if request can proceed (won't be rate limited).

        Args:
            bucket_name: Name of the bucket to check (default: "global")

        Returns:
            True if request can proceed, False if rate limited
        """
        if not self.enabled:
            return True

        bucket = self._get_bucket(bucket_name)
        can_proceed = bucket.consume()

        if not can_proceed:
            self._log_warning(f"Rate limit exceeded for bucket: {bucket_name}")

        return can_proceed

    def get_status(self, bucket_name: str = "global") -> RateLimitStatus:
        """
        Get current rate limit status for a bucket.

        Args:
            bucket_name: Name of the bucket to check

        Returns:
            RateLimitStatus with current state
        """
        if not self.enabled:
            return RateLimitStatus(
                requests_per_hour=self.global_requests_per_hour,
                current_requests=0,
                remaining_requests=self.global_requests_per_hour,
                time_until_reset_seconds=0.0,
                is_limited=False
            )

        bucket = self._get_bucket(bucket_name)
        return bucket.get_status()

    def wait_if_needed(self, bucket_name: str = "global", timeout_seconds: float = 30.0) -> bool:
        """
        Wait until request can proceed or timeout.

        Args:
            bucket_name: Name of the bucket to check
            timeout_seconds: Maximum time to wait

        Returns:
            True if can proceed, False if timeout reached
        """
        if not self.enabled:
            return True

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if self.can_proceed(bucket_name):
                return True

            # Wait a bit before checking again
            time.sleep(0.1)

        self._log_warning(f"Rate limit wait timeout for bucket: {bucket_name}")
        return False

    def reset(self, bucket_name: str = "global"):
        """
        Reset a specific bucket to full capacity.

        Args:
            bucket_name: Name of the bucket to reset
        """
        bucket = self._get_bucket(bucket_name)
        with bucket.lock:
            bucket.tokens = bucket.bucket_capacity
            bucket.last_refill = time.time()

    def _get_bucket(self, bucket_name: str) -> TokenBucket:
        """
        Get or create a token bucket for the given name.

        Args:
            bucket_name: Name of the bucket

        Returns:
            TokenBucket instance
        """
        with self.lock:
            if bucket_name not in self.buckets:
                # Create bucket with same configuration as global
                self.buckets[bucket_name] = TokenBucket(self.refill_rate, self.burst_size)
                self._log_info(f"Created rate limit bucket: {bucket_name}")

            return self.buckets[bucket_name]

    def get_all_statuses(self) -> Dict[str, RateLimitStatus]:
        """
        Get status for all buckets including global.

        Returns:
            Dictionary mapping bucket names to RateLimitStatus
        """
        statuses = {"global": self.get_status("global")}

        with self.lock:
            for bucket_name in self.buckets.keys():
                statuses[bucket_name] = self.get_status(bucket_name)

        return statuses

    def _log_info(self, message: str):
        """Log info message."""
        logger.info(f"RateLimiter: {message}")

    def _log_warning(self, message: str):
        """Log warning message."""
        logger.warning(f"RateLimiter: {message}")

    def _log_error(self, message: str):
        """Log error message."""
        logger.error(f"RateLimiter: {message}")


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get the global rate limiter instance.

    Returns:
        RateLimiter singleton instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter():
    """Reset the global rate limiter instance (useful for testing)."""
    global _rate_limiter
    _rate_limiter = None