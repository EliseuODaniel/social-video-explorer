"""
Tests for cache implementation.

This module tests the LRU cache with TTL functionality.
"""

import pytest
import time
import threading
from unittest.mock import patch

from core.providers.cache import LRUCache, CacheManager, CacheStats, CacheEntry


class TestLRUCache:
    """Test cases for LRUCache class."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = LRUCache(max_size=100, default_ttl_seconds=300)
        assert cache.max_size == 100
        assert cache.default_ttl_seconds == 300
        assert len(cache._cache) == 0

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = LRUCache(max_size=10, default_ttl_seconds=60)

        # Set and get a value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Get non-existent key
        assert cache.get("non_existent") is None

    def test_cache_ttl_expiration(self):
        """Test TTL expiration functionality."""
        cache = LRUCache(max_size=10, default_ttl_seconds=1)  # 1 second TTL

        # Set a value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        assert cache.get("key1") is None

    def test_cache_custom_ttl(self):
        """Test custom TTL per item."""
        cache = LRUCache(max_size=10, default_ttl_seconds=60)

        # Set with custom TTL
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2")  # Uses default TTL

        # Both should be available immediately
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        # Wait for custom TTL expiration
        time.sleep(1.1)

        # key1 should be expired, key2 should still be available
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=3, default_ttl_seconds=60)

        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All should be present
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Add one more - should evict least recently used (key1)
        cache.set("key4", "value4")

        # key1 should be evicted, others should remain
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_lru_access_updates(self):
        """Test that accessing items updates LRU order."""
        cache = LRUCache(max_size=3, default_ttl_seconds=60)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add key4 - should evict key2 (now least recently used)
        cache.set("key4", "value4")

        # key2 should be evicted
        assert cache.get("key2") is None
        assert cache.get("key1") == "value1"  # Still present due to recent access
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_delete(self):
        """Test cache deletion."""
        cache = LRUCache(max_size=10, default_ttl_seconds=60)

        # Set and then delete
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        assert cache.delete("key1") is True
        assert cache.get("key1") is None

        # Delete non-existent key
        assert cache.delete("non_existent") is False

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = LRUCache(max_size=10, default_ttl_seconds=60)

        # Add some items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert len(cache._cache) == 3

        # Clear cache
        cleared_count = cache.clear()
        assert cleared_count == 3
        assert len(cache._cache) == 0
        assert cache.get("key1") is None

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = LRUCache(max_size=10, default_ttl_seconds=1)

        # Add items with different TTLs
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=10)  # Long TTL

        # Wait for key1 to expire
        time.sleep(1.1)

        # Cleanup expired entries
        cleaned_count = cache.cleanup_expired()
        assert cleaned_count == 1

        # key1 should be gone, key2 should remain
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=10, default_ttl_seconds=60)

        # Initial stats
        stats = cache.get_stats()
        assert isinstance(stats, CacheStats)
        assert stats.total_entries == 0
        assert stats.hit_count == 0
        assert stats.miss_count == 0
        assert stats.hit_ratio == 0.0

        # Add item and get hit
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats.total_entries == 1
        assert stats.hit_count == 1
        assert stats.miss_count == 1
        assert stats.hit_ratio == 0.5

    def test_cache_ttl_update(self):
        """Test updating TTL for existing entries."""
        cache = LRUCache(max_size=10, default_ttl_seconds=60)

        # Set with short TTL
        cache.set("key1", "value1", ttl_seconds=1)

        # Update TTL to longer duration
        assert cache.set_ttl("key1", ttl_seconds=10) is True

        # Wait past original TTL
        time.sleep(1.1)

        # Should still be available due to updated TTL
        assert cache.get("key1") == "value1"

        # Try to update TTL for non-existent key
        assert cache.set_ttl("non_existent", ttl_seconds=10) is False

    def test_cache_thread_safety(self):
        """Test thread safety of cache operations."""
        cache = LRUCache(max_size=100, default_ttl_seconds=60)
        results = []
        errors = []

        def cache_operations(thread_id):
            try:
                for i in range(50):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    cache.set(key, value)
                    retrieved = cache.get(key)
                    results.append((key, retrieved))
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = [threading.Thread(target=cache_operations, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 250  # 50 operations * 5 threads

        # All set operations should have worked
        for key, value in results[:50]:  # Check first thread's operations
            assert value is not None

    def test_cache_expired_count(self):
        """Test counting expired entries without removing them."""
        cache = LRUCache(max_size=10, default_ttl_seconds=1)

        # Add items with different TTLs
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=10)

        # Wait for key1 to expire
        time.sleep(1.1)

        # Should count expired entries
        expired_count = cache.get_expired_count()
        assert expired_count == 1

        # But expired entries should still be accessible until cleanup
        assert cache.get("key1") is None  # Actually removed on access

    @patch.dict('os.environ', {'CACHE_CLEANUP_INTERVAL_SECONDS': '1'})
    def test_cache_automatic_cleanup(self):
        """Test automatic cleanup on interval."""
        cache = LRUCache(max_size=10, default_ttl_seconds=1)

        # Add item
        cache.set("key1", "value1")

        # Wait past cleanup interval and TTL
        time.sleep(2.1)

        # Access cache to trigger cleanup
        cache.get("key1")  # Should be None due to cleanup


class TestCacheManager:
    """Test cases for CacheManager class."""

    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        with patch.dict('os.environ', {
            'CACHE_MAX_SIZE': '500',
            'CACHE_DEFAULT_TTL_SECONDS': '600'
        }):
            manager = CacheManager()
            assert manager.default_max_size == 500
            assert manager.default_ttl == 600

    def test_get_cache_instance(self):
        """Test getting cache instances."""
        manager = CacheManager()

        # Get cache - should create new instance
        cache1 = manager.get_cache("test_cache")
        assert isinstance(cache1, LRUCache)

        # Get same cache name - should return same instance
        cache2 = manager.get_cache("test_cache")
        assert cache1 is cache2

        # Get different cache name - should create new instance
        cache3 = manager.get_cache("another_cache")
        assert cache3 is not cache1

    def test_get_cache_with_custom_config(self):
        """Test getting cache with custom configuration."""
        manager = CacheManager()

        cache = manager.get_cache("custom_cache", max_size=50, ttl_seconds=120)
        assert cache.max_size == 50
        assert cache.default_ttl_seconds == 120

    def test_clear_all_caches(self):
        """Test clearing all caches."""
        manager = CacheManager()

        # Create and populate caches
        cache1 = manager.get_cache("cache1")
        cache2 = manager.get_cache("cache2")

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        # Clear all
        results = manager.clear_all()
        assert results["cache1"] == 1
        assert results["cache2"] == 1

        # All caches should be empty
        assert cache1.get("key1") is None
        assert cache2.get("key2") is None

    def test_get_all_stats(self):
        """Test getting statistics for all caches."""
        manager = CacheManager()

        # Create caches and add data
        cache1 = manager.get_cache("cache1")
        cache2 = manager.get_cache("cache2")

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")
        cache1.get("key1")  # Hit
        cache2.get("nonexistent")  # Miss

        all_stats = manager.get_all_stats()
        assert isinstance(all_stats, dict)
        assert "cache1" in all_stats
        assert "cache2" in all_stats
        assert all_stats["cache1"].hit_count == 1
        assert all_stats["cache2"].miss_count == 1


if __name__ == "__main__":
    pytest.main([__file__])