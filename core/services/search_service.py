"""Basic search service for Social Video Explorer.

This module provides the main search functionality that orchestrates video providers
and returns normalized search results.
"""

import logging
from typing import Dict, Any, List, Optional

from ..providers.base import BaseVideoProvider, ProviderError
from ..providers.meta import MetaProvider
from ..providers.mock import MockProvider
from ..schemas import SearchParams, VideoResult, SearchResponse, VideoProvider

logger = logging.getLogger(__name__)


class SearchService:
    """Main search service for video discovery.

    Orchestrates multiple video providers to provide unified search functionality
    with fallback to mock mode when real providers are not available.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize search service with providers.

        Args:
            config: Service configuration including provider credentials
        """
        self.config = config or {}
        self._providers: Dict[VideoProvider, BaseVideoProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available providers."""
        # Initialize Meta provider
        meta_config = self.config.get('meta', {})
        meta_provider = MetaProvider(meta_config)
        self._providers[VideoProvider.META] = meta_provider

        # Initialize mock provider (always available)
        mock_provider = MockProvider()
        self._providers[VideoProvider.MOCK] = mock_provider

        logger.info(f"Initialized {len(self._providers)} providers: {list(self._providers.keys())}")

    def get_available_providers(self) -> List[VideoProvider]:
        """Get list of available providers.

        Returns:
            List of available provider types
        """
        available = []
        for provider_type, provider in self._providers.items():
            if provider.is_available():
                available.append(provider_type)
        return available

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about all providers.

        Returns:
            Dictionary with provider information and capabilities
        """
        info = {
            "total_providers": len(self._providers),
            "available_providers": self.get_available_providers(),
            "provider_details": {}
        }

        for provider_type, provider in self._providers.items():
            try:
                validation_errors = provider.validate_config()
                provider_info = provider.get_config_info()
                provider_info.update({
                    "validation_errors": validation_errors,
                    "is_configured": len(validation_errors) == 0
                })
                info["provider_details"][provider_type.value] = provider_info
            except Exception as e:
                logger.error(f"Error getting info for {provider_type}: {e}")
                info["provider_details"][provider_type.value] = {
                    "error": str(e),
                    "is_available": False
                }

        return info

    async def search(self, params: SearchParams) -> SearchResponse:
        """Search for videos using available providers.

        Args:
            params: Search parameters

        Returns:
            SearchResponse with results and metadata

        Raises:
            ValueError: If search parameters are invalid
            ProviderError: If all available providers fail
        """
        logger.info(f"Search request: query='{params.query}', max_results={params.max_results}")

        # Validate search parameters
        if not params.query or not params.query.strip():
            raise ValueError("Search query cannot be empty")

        # Determine which provider to use
        provider_to_use = self._select_provider(params.provider)
        # Handle both enum and string values due to Pydantic V2 conversion
        provider_name = provider_to_use.value if hasattr(provider_to_use, 'value') else str(provider_to_use)
        logger.info(f"Using provider: {provider_name}")

        try:
            # Perform search with selected provider (handle both enum and string)
            provider_key = provider_to_use if isinstance(provider_to_use, VideoProvider) else VideoProvider(provider_to_use)
            provider = self._providers[provider_key]
            results = await provider.search(params)

            # Create response
            response = SearchResponse(
                results=results,
                total_results=len(results),
                search_params=params,
                provider_used=provider_to_use,
                is_mock_mode=(provider_to_use == VideoProvider.MOCK)
            )

            # Handle both enum and string values for logging
            provider_name = provider_to_use.value if hasattr(provider_to_use, 'value') else str(provider_to_use)
            logger.info(f"Search completed: {len(results)} results from {provider_name}")
            return response

        except ProviderError as e:
            logger.error(f"Provider error during search: {e}")
            # Try to fallback to mock provider if not already using it
            if provider_to_use != VideoProvider.MOCK:
                logger.info("Falling back to mock provider")
                return await self._search_with_mock_fallback(params)
            else:
                raise

        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            # Handle provider_to_use conversion for error reporting
            error_provider = provider_to_use if isinstance(provider_to_use, VideoProvider) else VideoProvider(provider_to_use)
            raise ProviderError(
                f"Search failed: {str(e)}",
                error_provider,
                original_error=e
            )

    def _select_provider(self, requested_provider: Optional[VideoProvider]) -> VideoProvider:
        """Select which provider to use for search.

        Args:
            requested_provider: Specific provider requested (if any)

        Returns:
            Selected provider type

        Raises:
            ValueError: If no suitable provider is available
        """
        available = self.get_available_providers()

        # If specific provider requested and available, use it
        if requested_provider and requested_provider in available:
            return requested_provider

        # If specific provider requested but not available, check if it's Meta
        if requested_provider == VideoProvider.META:
            logger.warning("Meta provider requested but not available, falling back to mock")
            return VideoProvider.MOCK

        # Use first available provider, preferring non-mock if available
        non_mock_providers = [p for p in available if p != VideoProvider.MOCK]
        if non_mock_providers:
            return non_mock_providers[0]

        if VideoProvider.MOCK in available:
            return VideoProvider.MOCK

        raise ValueError("No suitable video providers available")

    async def _search_with_mock_fallback(self, params: SearchParams) -> SearchResponse:
        """Fallback search using mock provider.

        Args:
            params: Original search parameters

        Returns:
            SearchResponse with mock results
        """
        try:
            mock_provider = self._providers[VideoProvider.MOCK]
            results = await mock_provider.search(params)

            return SearchResponse(
                results=results,
                total_results=len(results),
                search_params=params,
                provider_used=VideoProvider.MOCK,
                is_mock_mode=True
            )

        except Exception as e:
            logger.error(f"Mock fallback also failed: {e}")
            raise ProviderError(
                "All providers including mock are unavailable",
                VideoProvider.MOCK,
                original_error=e
            )