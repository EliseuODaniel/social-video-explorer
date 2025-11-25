"""
Memory cache implementation with TTL and LRU eviction.

This module provides thread-safe caching with configurable TTL (Time To Live)
and LRU (Least Recently Used) eviction policies for efficient memory usage.
"""

import os
import time
import threading
import logging
from typing import Any, Dict, Optional, NamedTuple, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheEntry(NamedTuple):
    """Cache entry with value and expiration time."""
    value: Any
    expires_at: float
    created_at: float
    hit_count: int = 0


class CacheStats(NamedTuple):
    """Cache statistics."""
    total_entries: int
    hit_count: int
    miss_count: int
    hit_ratio: float
    memory_usage_bytes: int


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.

    Features:
    - LRU eviction when capacity is reached
    - Per-item TTL with automatic cleanup
    - Thread-safe operations
    - Cache statistics and metrics
    - Configurable cleanup intervals
    """

    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 900):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries to store
            default_ttl_seconds: Default TTL in seconds (15 minutes)
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds

        # OrderedDict provides O(1) LRU operations
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        # Cleanup configuration
        self.cleanup_interval = int(os.getenv("CACHE_CLEANUP_INTERVAL_SECONDS", "300"))  # 5 minutes
        self.last_cleanup = time.time()

        self._log_info(f"LRUCache initialized: max_size={max_size}, ttl={default_ttl_seconds}s")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            self._cleanup_if_needed()

            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]
            current_time = time.time()

            # Check if entry has expired
            if entry.expires_at <= current_time:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (mark as recently used)
            self._cache.move_to_end(key)

            # Update hit count
            updated_entry = entry._replace(hit_count=entry.hit_count + 1)
            self._cache[key] = updated_entry

            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Custom TTL in seconds (uses default if None)

        Returns:
            True if value was cached, False if evicted due to size
        """
        with self._lock:
            self._cleanup_if_needed()

            current_time = time.time()
            ttl = ttl_seconds or self.default_ttl_seconds
            expires_at = current_time + ttl

            entry = CacheEntry(
                value=value,
                expires_at=expires_at,
                created_at=current_time,
                hit_count=0
            )

            # Check if we need to evict entries
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Evict least recently used entry
                evicted_key, evicted_entry = self._cache.popitem(last=False)
                self._evictions += 1
                self._log_debug(f"Evicted cache entry: {evicted_key}")

            # Add or update entry
            self._cache[key] = entry
            self._cache.move_to_end(key)

            return True

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """
        Clear all entries from cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._log_info(f"Cleared {count} cache entries")
            return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.expires_at <= current_time
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self._log_debug(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats with current statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = self._hits / total_requests if total_requests > 0 else 0.0

            # Estimate memory usage (rough calculation)
            memory_usage = 0
            for key, entry in self._cache.items():
                memory_usage += len(key.encode('utf-8'))
                memory_usage += len(str(entry.value).encode('utf-8'))

            return CacheStats(
                total_entries=len(self._cache),
                hit_count=self._hits,
                miss_count=self._misses,
                hit_ratio=hit_ratio,
                memory_usage_bytes=memory_usage
            )

    def get_expired_count(self) -> int:
        """
        Count expired entries (without removing them).

        Returns:
            Number of expired entries
        """
        with self._lock:
            current_time = time.time()
            return sum(
                1 for entry in self._cache.values()
                if entry.expires_at <= current_time
            )

    def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """
        Update TTL for an existing cache entry.

        Args:
            key: Cache key
            ttl_seconds: New TTL in seconds

        Returns:
            True if TTL was updated, False if key not found
        """
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            current_time = time.time()
            new_expires_at = current_time + ttl_seconds

            updated_entry = entry._replace(expires_at=new_expires_at)
            self._cache[key] = updated_entry

            return True

    def _cleanup_if_needed(self):
        """Run cleanup if interval has passed."""
        current_time = time.time()
        if current_time - self.last_cleanup >= self.cleanup_interval:
            self.cleanup_expired()
            self.last_cleanup = current_time

    def _log_info(self, message: str):
        """Log info message."""
        logger.info(f"LRUCache: {message}")

    def _log_debug(self, message: str):
        """Log debug message."""
        logger.debug(f"LRUCache: {message}")

    def _log_warning(self, message: str):
        """Log warning message."""
        logger.warning(f"LRUCache: {message}")


# Cache manager for multiple cache instances
class CacheManager:
    """Manages multiple cache instances with different configurations."""

    def __init__(self):
        """Initialize cache manager."""
        self._caches: Dict[str, LRUCache] = {}
        self._lock = threading.Lock()

        # Default configurations from environment
        self.default_max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))
        self.default_ttl = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "900"))  # 15 minutes

        self._log_info("CacheManager initialized")

    def get_cache(self, cache_name: str, max_size: Optional[int] = None, ttl_seconds: Optional[int] = None) -> LRUCache:
        """
        Get or create a cache instance.

        Args:
            cache_name: Name of the cache
            max_size: Maximum size (uses default if None)
            ttl_seconds: Default TTL (uses default if None)

        Returns:
            LRUCache instance
        """
        with self._lock:
            if cache_name not in self._caches:
                size = max_size or self.default_max_size
                ttl = ttl_seconds or self.default_ttl

                self._caches[cache_name] = LRUCache(max_size=size, default_ttl_seconds=ttl)
                self._log_info(f"Created cache: {cache_name} (size={size}, ttl={ttl})")

            return self._caches[cache_name]

    def clear_all(self) -> Dict[str, int]:
        """
        Clear all caches.

        Returns:
            Dictionary mapping cache names to cleared entry count
        """
        results = {}
        with self._lock:
            for name, cache in self._caches.items():
                results[name] = cache.clear()

        return results

    def get_all_stats(self) -> Dict[str, CacheStats]:
        """
        Get statistics for all caches.

        Returns:
            Dictionary mapping cache names to CacheStats
        """
        stats = {}
        with self._lock:
            for name, cache in self._caches.items():
                stats[name] = cache.get_stats()

        return stats

    def cleanup_all(self) -> Dict[str, int]:
        """
        Cleanup expired entries in all caches.

        Returns:
            Dictionary mapping cache names to cleaned entry count
        """
        results = {}
        with self._lock:
            for name, cache in self._caches.items():
                results[name] = cache.cleanup_expired()

        return results

    def _log_info(self, message: str):
        """Log info message."""
        logger.info(f"CacheManager: {message}")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.

    Returns:
        CacheManager singleton instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_cache(cache_name: str, max_size: Optional[int] = None, ttl_seconds: Optional[int] = None) -> LRUCache:
    """
    Get a cache instance by name.

    Args:
        cache_name: Name of the cache
        max_size: Maximum size (uses default if None)
        ttl_seconds: Default TTL (uses default if None)

    Returns:
        LRUCache instance
    """
    manager = get_cache_manager()
    return manager.get_cache(cache_name, max_size, ttl_seconds)


def reset_cache_manager():
    """Reset the global cache manager instance (useful for testing)."""
    global _cache_manager
    _cache_manager = None