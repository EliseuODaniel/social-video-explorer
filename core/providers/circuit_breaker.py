"""
Circuit breaker implementation for fault tolerance.

This module provides circuit breaker patterns to prevent cascading failures
and provide automatic fallback when external services are unavailable.
"""

import os
import time
import threading
import logging
from typing import Optional, Callable, Any, NamedTuple
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerConfig(NamedTuple):
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Number of failures before opening
    success_threshold: int = 2          # Number of successes to close from half-open
    timeout_seconds: int = 60           # Time to wait before trying half-open
    recovery_timeout_seconds: int = 30  # Minimum time in half-open state
    exception_types: tuple = (Exception,)  # Exception types that trigger failure


class CircuitBreakerStats(NamedTuple):
    """Circuit breaker statistics."""
    state: CircuitState
    failure_count: int
    success_count: int
    total_requests: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    next_attempt_time: Optional[float]


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Features:
    - Automatic state transitions (closed -> open -> half-open -> closed)
    - Configurable failure/success thresholds
    - Time-based recovery
    - Thread-safe operations
    - Detailed statistics and metrics
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the circuit (for logging/metrics)
            config: Configuration options (uses defaults if None)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_requests = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._next_attempt_time: Optional[float] = None

        # Thread safety
        self._lock = threading.RLock()

        # Load configuration from environment if not provided
        if config is None:
            self._load_env_config()

        self._log_info(f"CircuitBreaker '{name}' initialized in {self._state.value} state")

    def _load_env_config(self):
        """Load configuration from environment variables."""
        prefix = f"CIRCUIT_BREAKER_{self.name.upper()}_"

        failure_threshold = int(os.getenv(f"{prefix}FAILURE_THRESHOLD", "5"))
        success_threshold = int(os.getenv(f"{prefix}SUCCESS_THRESHOLD", "2"))
        timeout_seconds = int(os.getenv(f"{prefix}TIMEOUT_SECONDS", "60"))
        recovery_timeout = int(os.getenv(f"{prefix}RECOVERY_TIMEOUT_SECONDS", "30"))

        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_seconds=timeout_seconds,
            recovery_timeout_seconds=recovery_timeout
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function through the circuit breaker.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function return value

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function call
        """
        with self._lock:
            if not self._can_execute():
                self._log_warning(f"Circuit '{self.name}' is OPEN, rejecting call")
                raise CircuitBreakerOpenError(f"Circuit '{self.name}' is open")

        # Attempt to execute the function
        start_time = time.time()
        try:
            self._total_requests += 1
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self._on_failure(e, execution_time)
            raise

    def async_call(self, coro_func: Callable, *args, **kwargs):
        """
        Call an async coroutine function through the circuit breaker.

        Args:
            coro_func: Async coroutine function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Coroutine that when awaited returns the function result
        """
        async def wrapper():
            with self._lock:
                if not self._can_execute():
                    self._log_warning(f"Circuit '{self.name}' is OPEN, rejecting async call")
                    raise CircuitBreakerOpenError(f"Circuit '{self.name}' is open")

            start_time = time.time()
            try:
                self._total_requests += 1
                result = await coro_func(*args, **kwargs)
                self._on_success()
                return result

            except Exception as e:
                execution_time = time.time() - start_time
                self._on_failure(e, execution_time)
                raise

        return wrapper()

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state

    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        with self._lock:
            return CircuitBreakerStats(
                state=self._state,
                failure_count=self._failure_count,
                success_count=self._success_count,
                total_requests=self._total_requests,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
                next_attempt_time=self._next_attempt_time
            )

    def reset(self):
        """Reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._last_success_time = None
            self._next_attempt_time = None
            self._log_info(f"Circuit '{self.name}' manually reset to CLOSED")

    def force_open(self):
        """Force circuit breaker to open state."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._next_attempt_time = time.time() + self.config.timeout_seconds
            self._log_info(f"Circuit '{self.name}' manually forced to OPEN")

    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.get_state() == CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.get_state() == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self.get_state() == CircuitState.HALF_OPEN

    def _can_execute(self) -> bool:
        """Check if execution should be allowed."""
        current_time = time.time()

        if self._state == CircuitState.CLOSED:
            return True

        elif self._state == CircuitState.OPEN:
            # Check if timeout has passed to try half-open
            if self._next_attempt_time and current_time >= self._next_attempt_time:
                self._transition_to_half_open()
                return True
            return False

        elif self._state == CircuitState.HALF_OPEN:
            return True

        return False

    def _on_success(self):
        """Handle successful execution."""
        current_time = time.time()
        self._last_success_time = current_time

        with self._lock:
            if self._state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                self._failure_count = max(0, self._failure_count - 1)

            elif self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()

    def _on_failure(self, exception: Exception, execution_time: float):
        """Handle failed execution."""
        current_time = time.time()
        self._last_failure_time = current_time

        # Check if this exception type should trigger circuit breaker
        should_count = isinstance(exception, self.config.exception_types)
        if not should_count:
            return

        with self._lock:
            if self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

            elif self._state == CircuitState.HALF_OPEN:
                self._transition_to_open()

        self._log_debug(f"Circuit '{self.name}' failure: {exception.__class__.__name__}: {str(exception)}")

    def _transition_to_closed(self):
        """Transition to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._next_attempt_time = None
        self._log_info(f"Circuit '{self.name}' transitioned to CLOSED")

    def _transition_to_open(self):
        """Transition to open state."""
        self._state = CircuitState.OPEN
        self._next_attempt_time = time.time() + self.config.timeout_seconds
        self._success_count = 0
        self._log_warning(f"Circuit '{self.name}' transitioned to OPEN (failures: {self._failure_count})")

    def _transition_to_half_open(self):
        """Transition to half-open state."""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        self._log_info(f"Circuit '{self.name}' transitioned to HALF_OPEN")

    def _log_info(self, message: str):
        """Log info message."""
        logger.info(f"CircuitBreaker[{self.name}]: {message}")

    def _log_warning(self, message: str):
        """Log warning message."""
        logger.warning(f"CircuitBreaker[{self.name}]: {message}")

    def _log_debug(self, message: str):
        """Log debug message."""
        logger.debug(f"CircuitBreaker[{self.name}]: {message}")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Circuit breaker manager for multiple instances
class CircuitBreakerManager:
    """Manages multiple circuit breaker instances."""

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            name: Name of the circuit breaker
            config: Configuration (uses defaults if None)

        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]

    def get_all_stats(self) -> dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        stats = {}
        with self._lock:
            for name, breaker in self._breakers.items():
                stats[name] = breaker.get_stats()
        return stats

    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()

    def force_open_all(self):
        """Force all circuit breakers to open."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.force_open()


# Global circuit breaker manager instance
_circuit_manager: Optional[CircuitBreakerManager] = None


def get_circuit_manager() -> CircuitBreakerManager:
    """
    Get the global circuit breaker manager instance.

    Returns:
        CircuitBreakerManager singleton instance
    """
    global _circuit_manager
    if _circuit_manager is None:
        _circuit_manager = CircuitBreakerManager()
    return _circuit_manager


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get a circuit breaker by name.

    Args:
        name: Name of the circuit breaker
        config: Configuration (uses defaults if None)

    Returns:
        CircuitBreaker instance
    """
    manager = get_circuit_manager()
    return manager.get_breaker(name, config)


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator to apply circuit breaker to a function.

    Args:
        name: Name of the circuit breaker
        config: Circuit breaker configuration
    """
    breaker = get_circuit_breaker(name, config)

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper

    return decorator


def async_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator to apply circuit breaker to an async function.

    Args:
        name: Name of the circuit breaker
        config: Circuit breaker configuration
    """
    breaker = get_circuit_breaker(name, config)

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            return await breaker.async_call(func, *args, **kwargs)
        return wrapper

    return decorator


def reset_circuit_manager():
    """Reset the global circuit breaker manager (useful for testing)."""
    global _circuit_manager
    _circuit_manager = None