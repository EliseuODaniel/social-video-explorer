"""
Tests for rate limiter implementation.

This module tests the token bucket algorithm and rate limiting functionality.
"""

import pytest
import time
import threading
from unittest.mock import patch

from core.providers.rate_limiter import RateLimiter, TokenBucket, RateLimitStatus


class TestTokenBucket:
    """Test cases for TokenBucket class."""

    def test_token_bucket_initialization(self):
        """Test token bucket initialization."""
        bucket = TokenBucket(refill_rate=1.0, bucket_capacity=10)
        assert bucket.tokens == bucket.bucket_capacity == 10
        assert bucket.refill_rate == 1.0

    def test_token_bucket_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(refill_rate=1.0, bucket_capacity=10)
        assert bucket.consume(1) is True
        assert bucket.tokens == 9

    def test_token_bucket_consume_multiple(self):
        """Test consuming multiple tokens."""
        bucket = TokenBucket(refill_rate=1.0, bucket_capacity=10)
        assert bucket.consume(5) is True
        assert bucket.tokens == 5

    def test_token_bucket_consume_insufficient(self):
        """Test token consumption with insufficient tokens."""
        bucket = TokenBucket(refill_rate=1.0, bucket_capacity=5)
        # Consume all tokens
        assert bucket.consume(5) is True
        assert bucket.tokens <= 0.0001  # Account for floating point precision

        # Try to consume more
        assert bucket.consume(1) is False
        assert bucket.tokens <= 0.0001  # Should remain at or near 0

    def test_token_bucket_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(refill_rate=10.0, bucket_capacity=10)  # 10 tokens per second

        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens <= 0.0001

        # Wait for refill (0.2 second = 2 tokens)
        time.sleep(0.25)  # Slightly more to account for timing

        # Check tokens after refill (trigger refill check)
        status = bucket.get_status()
        # Should have some tokens now
        assert status.remaining_requests >= 1.5  # Should have ~2 tokens
        assert status.remaining_requests <= bucket.bucket_capacity

    def test_token_bucket_thread_safety(self):
        """Test thread safety of token bucket operations."""
        bucket = TokenBucket(refill_rate=100.0, bucket_capacity=100)
        results = []

        def consume_tokens():
            for _ in range(50):
                result = bucket.consume(1)
                results.append(result)

        # Run multiple threads
        threads = [threading.Thread(target=consume_tokens) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have consumed exactly 250 tokens (50 * 5 threads)
        # Starting from 100 tokens, so 150 failed consumptions
        success_count = sum(results)
        assert success_count <= 100  # Can't consume more than bucket capacity
        assert len(results) == 250  # All attempts recorded

    def test_token_bucket_status(self):
        """Test getting token bucket status."""
        bucket = TokenBucket(refill_rate=10.0, bucket_capacity=10)
        status = bucket.get_status()

        assert isinstance(status, RateLimitStatus)
        assert status.requests_per_hour == bucket.bucket_capacity == 10
        assert status.remaining_requests == 10
        assert status.current_requests == 0
        assert status.is_limited is False

        # Consume some tokens
        bucket.consume(3)
        status = bucket.get_status()
        assert status.remaining_requests == 7
        assert status.current_requests == 3

    def test_token_bucket_reset(self):
        """Test resetting token bucket."""
        bucket = TokenBucket(refill_rate=1.0, bucket_capacity=10)

        # Consume some tokens
        bucket.consume(5)
        assert abs(bucket.tokens - 5) < 0.0001

        # Reset
        bucket.reset()
        assert bucket.tokens == bucket.bucket_capacity == 10


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        with patch.dict('os.environ', {
            'RATE_LIMIT_REQUESTS_PER_HOUR': '300',
            'RATE_LIMIT_BURST_SIZE': '20'
        }):
            limiter = RateLimiter()
            assert limiter.global_requests_per_hour == 300
            assert limiter.burst_size == 20
            assert limiter.enabled is True

    def test_rate_limiter_disabled(self):
        """Test rate limiter when disabled."""
        with patch.dict('os.environ', {'RATE_LIMIT_ENABLED': 'false'}):
            limiter = RateLimiter()
            assert limiter.enabled is False
            assert limiter.can_proceed() is True  # Always true when disabled

    def test_rate_limiter_can_proceed(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter()
        limiter.global_requests_per_hour = 10
        limiter.burst_size = 5
        limiter.refill_rate = 1000.0  # Much higher rate for testing
        limiter.global_bucket = TokenBucket(limiter.refill_rate, limiter.burst_size)

        # Should be able to proceed initially
        assert limiter.can_proceed() is True

        # Consume all tokens
        for _ in range(5):
            assert limiter.can_proceed() is True

        # Should be rate limited now
        assert limiter.can_proceed() is False

    def test_rate_limiter_multiple_buckets(self):
        """Test multiple rate limiter buckets."""
        limiter = RateLimiter()
        limiter.global_requests_per_hour = 10
        limiter.burst_size = 5
        limiter.refill_rate = limiter.global_requests_per_hour / 3600.0

        # Consume from global bucket
        for _ in range(5):
            limiter.can_proceed()
        assert limiter.can_proceed() is False

        # But should still be able to proceed with different bucket
        assert limiter.can_proceed("test_bucket") is True

    def test_rate_limiter_wait_if_needed(self):
        """Test wait functionality."""
        limiter = RateLimiter()
        limiter.global_requests_per_hour = 10
        limiter.burst_size = 5
        limiter.refill_rate = limiter.global_requests_per_hour / 3600.0
        limiter.global_bucket = TokenBucket(limiter.refill_rate, limiter.burst_size)

        # Consume all tokens
        for _ in range(5):
            limiter.can_proceed()

        # Wait should fail immediately when rate limited
        start_time = time.time()
        result = limiter.wait_if_needed(timeout_seconds=0.1)
        elapsed = time.time() - start_time

        assert result is False
        assert elapsed < 0.2  # Should return quickly

    def test_rate_limiter_status(self):
        """Test getting rate limiter status."""
        limiter = RateLimiter()
        status = limiter.get_status()

        assert isinstance(status, RateLimitStatus)
        assert status.requests_per_hour > 0
        assert status.remaining_requests >= 0
        assert status.current_requests >= 0
        assert isinstance(status.is_limited, bool)

    def test_rate_limiter_disabled_status(self):
        """Test status when rate limiter is disabled."""
        with patch.dict('os.environ', {'RATE_LIMIT_ENABLED': 'false'}):
            limiter = RateLimiter()
            status = limiter.get_status()

            assert status.is_limited is False
            assert status.remaining_requests == limiter.global_requests_per_hour
            assert status.time_until_reset_seconds == 0.0

    def test_rate_limiter_all_statuses(self):
        """Test getting all bucket statuses."""
        limiter = RateLimiter()

        # Use multiple buckets
        limiter.can_proceed("bucket1")
        limiter.can_proceed("bucket2")
        limiter.can_proceed("bucket2")

        all_statuses = limiter.get_all_statuses()

        assert isinstance(all_statuses, dict)
        assert "global" in all_statuses
        assert "bucket1" in all_statuses
        assert "bucket2" in all_statuses

        # Check that bucket2 has more usage than bucket1
        assert all_statuses["bucket2"].current_requests >= all_statuses["bucket1"].current_requests


if __name__ == "__main__":
    pytest.main([__file__])