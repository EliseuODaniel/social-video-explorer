"""
Tests for circuit breaker implementation.

This module tests the circuit breaker fault tolerance patterns.
"""

import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock

from core.providers.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    circuit_breaker,
    async_circuit_breaker
)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker("test_breaker")
        assert breaker.name == "test_breaker"
        assert breaker._state == CircuitState.CLOSED
        assert breaker._failure_count == 0
        assert breaker._success_count == 0

    def test_circuit_breaker_custom_config(self):
        """Test circuit breaker with custom configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=5,
            timeout_seconds=120
        )
        breaker = CircuitBreaker("test_breaker", config)
        assert breaker.config.failure_threshold == 3
        assert breaker.config.success_threshold == 5
        assert breaker.config.timeout_seconds == 120

    @patch.dict('os.environ', {
        'CIRCUIT_BREAKER_TEST_BREAKER_FAILURE_THRESHOLD': '2',
        'CIRCUIT_BREAKER_TEST_BREAKER_SUCCESS_THRESHOLD': '3',
        'CIRCUIT_BREAKER_TEST_BREAKER_TIMEOUT_SECONDS': '45'
    })
    def test_circuit_breaker_env_config(self):
        """Test circuit breaker configuration from environment."""
        breaker = CircuitBreaker("test_breaker")
        assert breaker.config.failure_threshold == 2
        assert breaker.config.success_threshold == 3
        assert breaker.config.timeout_seconds == 45

    def test_circuit_breaker_closed_success(self):
        """Test successful call in closed state."""
        breaker = CircuitBreaker("test_breaker")
        mock_func = MagicMock(return_value="success")

        result = breaker.call(mock_func)
        assert result == "success"
        mock_func.assert_called_once()
        assert breaker._state == CircuitState.CLOSED

    def test_circuit_breaker_closed_failure_threshold(self):
        """Test circuit breaker opening after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=1)
        breaker = CircuitBreaker("test_breaker", config)
        mock_func = MagicMock(side_effect=Exception("Test error"))

        # First failure
        with pytest.raises(Exception):
            breaker.call(mock_func)
        assert breaker._failure_count == 1
        assert breaker._state == CircuitState.CLOSED

        # Second failure - should open circuit
        with pytest.raises(Exception):
            breaker.call(mock_func)
        assert breaker._failure_count == 2
        assert breaker._state == CircuitState.OPEN

    def test_circuit_breaker_open_rejection(self):
        """Test that calls are rejected when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout_seconds=1)
        breaker = CircuitBreaker("test_breaker", config)
        mock_func = MagicMock(return_value="success")

        # Force circuit open
        breaker._transition_to_open()

        # Call should be rejected without calling function
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(mock_func)
        mock_func.assert_not_called()

    def test_circuit_breaker_timeout_to_half_open(self):
        """Test circuit transition to half-open after timeout."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout_seconds=0.1, recovery_timeout_seconds=0.1)
        breaker = CircuitBreaker("test_breaker", config)

        # Force circuit open
        breaker._transition_to_open()
        assert breaker._state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Next call should attempt transition to half-open
        mock_func = MagicMock(return_value="success")
        result = breaker.call(mock_func)

        assert result == "success"
        assert breaker._state == CircuitState.HALF_OPEN

    def test_circuit_breaker_half_open_success_to_closed(self):
        """Test circuit transition to closed after successes in half-open."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout_seconds=0.1
        )
        breaker = CircuitBreaker("test_breaker", config)
        mock_func = MagicMock(return_value="success")

        # Move to half-open state
        breaker._transition_to_half_open()

        # First success
        breaker.call(mock_func)
        assert breaker._state == CircuitState.HALF_OPEN
        assert breaker._success_count == 1

        # Second success - should close circuit
        breaker.call(mock_func)
        assert breaker._state == CircuitState.CLOSED
        assert breaker._success_count == 0
        assert breaker._failure_count == 0

    def test_circuit_breaker_half_open_failure_to_open(self):
        """Test circuit transition back to open on failure in half-open."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout_seconds=0.1)
        breaker = CircuitBreaker("test_breaker", config)
        mock_func = MagicMock(side_effect=Exception("Test error"))

        # Move to half-open state
        breaker._transition_to_half_open()

        # Failure in half-open should open circuit again
        with pytest.raises(Exception):
            breaker.call(mock_func)

        assert breaker._state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_async_call(self):
        """Test async function calls through circuit breaker."""
        breaker = CircuitBreaker("test_breaker")

        async def async_func():
            await asyncio.sleep(0.01)
            return "async_success"

        result = await breaker.async_call(async_func)
        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_async_call_failure(self):
        """Test async function failure handling."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test_breaker", config)

        async def async_func():
            await asyncio.sleep(0.01)
            raise Exception("Async error")

        with pytest.raises(Exception):
            await breaker.async_call(async_func)

        assert breaker._failure_count == 1
        assert breaker._state == CircuitState.OPEN  # Opens after threshold=1

    def test_circuit_breaker_stats(self):
        """Test circuit breaker statistics."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test_breaker", config)

        # Record some activity - use direct internal access for controlled testing
        breaker._total_requests = 2
        breaker._failure_count = 1
        breaker._success_count = 1
        breaker._last_failure_time = time.time()
        breaker._last_success_time = time.time()

        stats = breaker.get_stats()
        assert stats.state == CircuitState.CLOSED
        assert stats.failure_count == 1
        assert stats.total_requests == 2
        assert stats.last_failure_time is not None
        assert stats.last_success_time is not None

    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test_breaker", config)

        # Cause failure to change state
        with pytest.raises(Exception):
            breaker.call(MagicMock(side_effect=Exception("error")))
        assert breaker._failure_count == 1

        # Reset circuit
        breaker.reset()
        assert breaker._state == CircuitState.CLOSED
        assert breaker._failure_count == 0
        assert breaker._success_count == 0

    def test_circuit_breaker_force_open(self):
        """Test forcing circuit breaker open."""
        breaker = CircuitBreaker("test_breaker")
        breaker.force_open()

        assert breaker._state == CircuitState.OPEN
        assert breaker._next_attempt_time is not None

    def test_circuit_breaker_state_checks(self):
        """Test circuit breaker state check methods."""
        breaker = CircuitBreaker("test_breaker")

        assert breaker.is_closed() is True
        assert breaker.is_open() is False
        assert breaker.is_half_open() is False

        breaker._transition_to_open()
        assert breaker.is_closed() is False
        assert breaker.is_open() is True
        assert breaker.is_half_open() is False

        breaker._transition_to_half_open()
        assert breaker.is_closed() is False
        assert breaker.is_open() is False
        assert breaker.is_half_open() is True

    def test_circuit_breaker_exception_filtering(self):
        """Test that only configured exception types trigger circuit breaker."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            exception_types=(ValueError,)  # Only ValueError triggers
        )
        breaker = CircuitBreaker("test_breaker", config)

        # Should not trigger circuit breaker
        with pytest.raises(Exception):
            breaker.call(MagicMock(side_effect=Exception("Other error")))

        assert breaker._failure_count == 0
        assert breaker._state == CircuitState.CLOSED

        # Should trigger circuit breaker
        with pytest.raises(ValueError):
            breaker.call(MagicMock(side_effect=ValueError("Value error")))

        assert breaker._failure_count == 1


class TestCircuitBreakerManager:
    """Test cases for CircuitBreakerManager class."""

    def test_manager_get_breaker(self):
        """Test getting circuit breaker from manager."""
        manager = CircuitBreakerManager()

        # Get breaker - should create new one
        breaker1 = manager.get_breaker("test_breaker")
        assert isinstance(breaker1, CircuitBreaker)
        assert breaker1.name == "test_breaker"

        # Get same name - should return same instance
        breaker2 = manager.get_breaker("test_breaker")
        assert breaker1 is breaker2

        # Get different name - should create new instance
        breaker3 = manager.get_breaker("another_breaker")
        assert breaker3 is not breaker1

    def test_manager_get_breaker_with_config(self):
        """Test getting circuit breaker with custom configuration."""
        manager = CircuitBreakerManager()
        config = CircuitBreakerConfig(failure_threshold=10)

        breaker = manager.get_breaker("custom_breaker", config)
        assert breaker.config.failure_threshold == 10

    def test_manager_get_all_stats(self):
        """Test getting statistics for all breakers."""
        manager = CircuitBreakerManager()

        # Create breakers
        breaker1 = manager.get_breaker("breaker1")
        breaker2 = manager.get_breaker("breaker2")

        # Simulate some activity
        breaker1.call(MagicMock(return_value="success"))
        with pytest.raises(Exception):
            breaker2.call(MagicMock(side_effect=Exception("error")))

        all_stats = manager.get_all_stats()
        assert isinstance(all_stats, dict)
        assert "breaker1" in all_stats
        assert "breaker2" in all_stats

    def test_manager_reset_all(self):
        """Test resetting all circuit breakers."""
        manager = CircuitBreakerManager()

        # Create and modify breakers
        breaker1 = manager.get_breaker("breaker1")
        breaker2 = manager.get_breaker("breaker2")

        breaker1.force_open()
        breaker2.force_open()

        # Reset all
        manager.reset_all()

        assert breaker1.is_closed()
        assert breaker2.is_closed()

    def test_manager_force_open_all(self):
        """Test forcing all circuit breakers open."""
        manager = CircuitBreakerManager()

        # Create breakers
        breaker1 = manager.get_breaker("breaker1")
        breaker2 = manager.get_breaker("breaker2")

        # Force all open
        manager.force_open_all()

        assert breaker1.is_open()
        assert breaker2.is_open()


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_circuit_breaker(self):
        """Test global circuit breaker getter."""
        breaker1 = get_circuit_breaker("global_test")
        breaker2 = get_circuit_breaker("global_test")
        breaker3 = get_circuit_breaker("another_global_test")

        assert isinstance(breaker1, CircuitBreaker)
        assert breaker1 is breaker2  # Same instance
        assert breaker1 is not breaker3  # Different instance

    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        mock_func = MagicMock(return_value="decorated_success")

        @circuit_breaker("decorator_test")
        def decorated_function():
            return mock_func()

        result = decorated_function()
        assert result == "decorated_success"
        mock_func.assert_called_once()

    def test_circuit_breaker_decorator_failure(self):
        """Test circuit breaker decorator with failure."""
        config = CircuitBreakerConfig(failure_threshold=1)
        mock_func = MagicMock(side_effect=Exception("Decorator error"))

        @circuit_breaker("decorator_failure_test", config)
        def failing_function():
            return mock_func()

        with pytest.raises(Exception):
            failing_function()

        # Should have recorded failure
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_decorator(self):
        """Test async circuit breaker decorator."""
        mock_func = MagicMock(return_value="async_decorated_success")

        @async_circuit_breaker("async_decorator_test")
        async def async_decorated_function():
            return mock_func()

        result = await async_decorated_function()
        assert result == "async_decorated_success"
        mock_func.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])