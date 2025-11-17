"""Base video provider interface.

This module defines the abstract interface that all video providers must implement,
providing a standardized way to integrate with different video platforms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from ..schemas import SearchParams, VideoResult, VideoProvider


class ProviderCapabilities:
    """Defines the capabilities of a video provider."""

    def __init__(
        self,
        supports_search: bool = True,
        supports_pagination: bool = False,
        max_results_per_search: int = 50,
        requires_authentication: bool = False,
        supported_filters: Optional[List[str]] = None
    ):
        """Initialize provider capabilities.

        Args:
            supports_search: Whether provider supports video search
            supports_pagination: Whether provider supports pagination
            max_results_per_search: Maximum results per search request
            requires_authentication: Whether provider requires API credentials
            supported_filters: List of supported filter types
        """
        self.supports_search = supports_search
        self.supports_pagination = supports_pagination
        self.max_results_per_search = max_results_per_search
        self.requires_authentication = requires_authentication
        self.supported_filters = supported_filters or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert capabilities to dictionary representation."""
        return {
            "supports_search": self.supports_search,
            "supports_pagination": self.supports_pagination,
            "max_results_per_search": self.max_results_per_search,
            "requires_authentication": self.requires_authentication,
            "supported_filters": self.supported_filters
        }


class BaseVideoProvider(ABC):
    """Abstract base class for video providers.

    All video providers must inherit from this class and implement the required methods.
    This ensures consistent interface across different video platforms.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the provider with configuration.

        Args:
            config: Provider-specific configuration (API keys, settings, etc.)
        """
        self.config = config or {}
        self._provider_type: Optional[VideoProvider] = None

    @property
    @abstractmethod
    def provider_type(self) -> VideoProvider:
        """Return the provider type enum value."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Return the capabilities of this provider.

        Returns:
            ProviderCapabilities object describing what this provider can do
        """
        pass

    @abstractmethod
    async def search(self, params: SearchParams) -> List[VideoResult]:
        """Search for videos using this provider.

        Args:
            params: Search parameters including query and limits

        Returns:
            List of VideoResult objects matching the search criteria

        Raises:
            ProviderError: If search fails due to API issues or invalid parameters
        """
        pass

    def is_available(self) -> bool:
        """Check if provider is available for use.

        Returns:
            True if provider has required configuration and can be used
        """
        return True

    def validate_config(self) -> List[str]:
        """Validate provider configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        capabilities = self.get_capabilities()

        if capabilities.requires_authentication:
            if not self._has_required_credentials():
                errors.append(
                    f"{self.provider_type.value} provider requires authentication "
                    "credentials but none were provided"
                )

        return errors

    def _has_required_credentials(self) -> bool:
        """Check if required authentication credentials are present.

        Override in subclasses to implement specific credential validation.
        """
        return True

    def get_config_info(self) -> Dict[str, Any]:
        """Get provider configuration information (safe for logging).

        Returns:
            Dictionary with non-sensitive configuration information
        """
        capabilities = self.get_capabilities()
        return {
            "provider_type": self.provider_type.value,
            "is_available": self.is_available(),
            "requires_authentication": capabilities.requires_authentication,
            "max_results": capabilities.max_results_per_search
        }


class ProviderError(Exception):
    """Exception raised by video providers."""

    def __init__(self, message: str, provider_type: VideoProvider, original_error: Optional[Exception] = None):
        """Initialize provider error.

        Args:
            message: Error message
            provider_type: Type of provider that raised the error
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.provider_type = provider_type
        self.original_error = original_error

    def __str__(self) -> str:
        """String representation of provider error."""
        base_msg = f"[{self.provider_type.value.upper()}] {super().__str__()}"
        if self.original_error:
            base_msg += f" (caused by: {type(self.original_error).__name__}: {self.original_error})"
        return base_msg