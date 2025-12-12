"""
Cache Strategy Implementation

Provides LRU (Least Recently Used) caching for memory optimization.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from collections import OrderedDict
from threading import RLock


class CacheStrategy(ABC):
    """Abstract base class for cache strategies."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def size(self) -> int:
        """Get current cache size."""
        pass


class LRUCache(CacheStrategy):
    """
    Thread-safe LRU (Least Recently Used) cache implementation.

    Evicts least recently used items when max_size is reached.
    Uses OrderedDict for O(1) access and updates.

    Attributes:
        max_size: Maximum number of items in cache
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache

        Raises:
            ValueError: If max_size <= 0
        """
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")

        self._max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = RLock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache and mark as recently used.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self._lock:
            if key not in self._cache:
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, value: Any) -> None:
        """
        Put value in cache.

        If cache is full, removes least recently used item.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Update existing key
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
                return

            # Add new key
            self._cache[key] = value
            self._cache.move_to_end(key)

            # Evict LRU if over capacity
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)  # Remove first (oldest)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """
        Get current number of cached items.

        Returns:
            Number of items in cache
        """
        with self._lock:
            return len(self._cache)

    def contains(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        with self._lock:
            return key in self._cache

    def remove(self, key: str) -> bool:
        """
        Remove specific key from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if key was removed, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'utilization': len(self._cache) / self._max_size if self._max_size > 0 else 0
            }

    def __len__(self) -> int:
        """Get cache size (for convenience)."""
        return self.size()

    def __contains__(self, key: str) -> bool:
        """Check if key exists (for convenience)."""
        return self.contains(key)

    def __str__(self) -> str:
        """String representation for logging."""
        with self._lock:
            return f"LRUCache(size={len(self._cache)}/{self._max_size})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"LRUCache(max_size={self._max_size}, current_size={len(self._cache)})"
