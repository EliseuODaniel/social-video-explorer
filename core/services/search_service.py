"""
Search service implementation

This module provides the main search service that coordinates multiple video
providers, handles fallback logic, and manages concurrent searches.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

from ..schemas import (
    SearchParams,
    SearchResponse,
    VideoResult,
    Platform,
    MediaType,
    ProviderStatus,
    SystemHealth,
)
from ..providers import BaseVideoProvider, MetaProvider, MockMetaProvider
from ..providers.oauth_client import MetaOAuth2Client
from ..providers.cache import LRUCache, get_cache
from ..providers.rate_limiter import RateLimiter, get_rate_limiter

logger = logging.getLogger(__name__)


class SearchService:
    """
    Main search service that coordinates multiple video providers
    and handles fallback mechanisms.
    """

    def __init__(self):
        """Initialize search service with appropriate providers."""
        self.production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
        self.providers: Dict[Platform, BaseVideoProvider] = {}
        self.oauth_client: Optional[MetaOAuth2Client] = None

        # Initialize caching and rate limiting
        self.search_cache = get_cache("search_results", max_size=200, ttl_seconds=900)  # 15 min TTL
        self.rate_limiter = get_rate_limiter()

        self._initialize_providers()
        self._log_info(
            f"SearchService initialized in {'production' if self.production_mode else 'mock'} mode with caching"
        )

    def _initialize_providers(self):
        """Initialize providers based on configuration."""
        try:
            if self.production_mode:
                # Initialize real OAuth client and Meta provider
                self.oauth_client = MetaOAuth2Client()
                meta_provider = MetaProvider(self.oauth_client)
                self.providers[Platform.META] = meta_provider
                self.providers[Platform.INSTAGRAM] = meta_provider
                self.providers[Platform.FACEBOOK] = meta_provider
                self._log_info("Production mode: Initialized real Meta provider")
            else:
                # Initialize mock providers
                mock_provider = MockMetaProvider()
                self.providers[Platform.META] = mock_provider
                self.providers[Platform.INSTAGRAM] = mock_provider
                self.providers[Platform.FACEBOOK] = mock_provider
                self._log_info("Mock mode: Initialized mock providers")

        except Exception as e:
            # Fallback to mock providers on initialization failure
            logger.error(f"Failed to initialize production providers: {e}")
            self._fallback_to_mock()

    def _fallback_to_mock(self):
        """Fallback to mock providers when production initialization fails."""
        self._log_warning("Falling back to mock providers")
        mock_provider = MockMetaProvider()
        self.providers[Platform.META] = mock_provider
        self.providers[Platform.INSTAGRAM] = mock_provider
        self.providers[Platform.FACEBOOK] = mock_provider
        self.production_mode = False

    async def search(self, params: SearchParams) -> SearchResponse:
        """
        Perform search across appropriate providers with cache-first strategy and fallback logic.

        Args:
            params: Search parameters

        Returns:
            SearchResponse with results and metadata
        """
        start_time = datetime.now()

        # Create cache key based on search parameters
        cache_key = self._create_cache_key(params)

        # Check cache first
        cached_response = self.search_cache.get(cache_key)
        if cached_response is not None:
            self._log_info(f"Cache hit for search: {params.query}")
            # Update cache metadata
            cached_response.search_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return cached_response

        # Check rate limiting before proceeding
        if not self.rate_limiter.can_proceed("search"):
            self._log_warning("Rate limited for search request")
            # Return cached results if available, otherwise empty response
            return SearchResponse(
                results=[],
                total_found=0,
                search_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                platforms_searched=[],
                query_used=params.query,
                errors=["Rate limit exceeded - try again later"],
            )

        all_results: List[VideoResult] = []
        platforms_searched: Set[Platform] = set()
        errors: List[str] = []

        try:
            # Determine which platforms to search
            platforms = self._get_platforms_to_search(params.platform)

            # Search each platform concurrently
            search_tasks = []
            for platform in platforms:
                if platform in self.providers:
                    task = self._search_platform_with_fallback(
                        self.providers[platform], params
                    )
                    search_tasks.append(task)

            if search_tasks:
                # Wait for all searches to complete
                platform_results = await asyncio.gather(
                    *search_tasks, return_exceptions=True
                )

                # Process results
                for i, result in enumerate(platform_results):
                    platform = list(platforms)[i] if i < len(platforms) else None

                    if isinstance(result, Exception):
                        error_msg = f"Error searching {platform.value if platform else 'unknown'}: {str(result)}"
                        errors.append(error_msg)
                        self._log_error(result, f"platform search for {platform}")
                    else:
                        platform_results_list = (
                            result if isinstance(result, list) else []
                        )
                        all_results.extend(platform_results_list)
                        if platform:
                            platforms_searched.add(platform)

                        self._log_info(
                            f"Found {len(platform_results_list)} results from {platform.value if platform else 'unknown'}"
                        )

            # Sort and limit results
            all_results = self._sort_and_limit_results(all_results, params)

            # Calculate search time
            search_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            response = SearchResponse(
                results=all_results,
                total_found=len(all_results),
                search_time_ms=search_time_ms,
                platforms_searched=list(platforms_searched),
                has_more=len(all_results) >= params.max_results,
                query_used=params.query,
                errors=errors,
            )

            # Cache the response (with different TTL based on query type)
            ttl_seconds = self._get_cache_ttl(params)
            self.search_cache.set(cache_key, response, ttl_seconds=ttl_seconds)

            self._log_info(
                f"Search completed: {len(all_results)} results in {search_time_ms}ms (cached for {ttl_seconds}s)"
            )
            return response

        except Exception as e:
            self._log_error(e, "search service")
            errors.append(f"Search service error: {str(e)}")

            return SearchResponse(
                results=[],
                total_found=0,
                search_time_ms=int(
                    (datetime.now() - start_time).total_seconds() * 1000
                ),
                platforms_searched=[],
                query_used=params.query,
                errors=errors,
            )

    def _create_cache_key(self, params: SearchParams) -> str:
        """
        Create a cache key from search parameters.

        Args:
            params: Search parameters

        Returns:
            String cache key
        """
        key_parts = [
            f"query:{params.query or 'empty'}",
            f"platform:{params.platform.value if hasattr(params.platform, 'value') else params.platform}",
            f"max_results:{params.max_results}",
            f"sort_by:{params.sort_by}",
            f"media_type:{params.media_type.value if params.media_type and hasattr(params.media_type, 'value') else (params.media_type or 'all')}",
        ]

        return "|".join(key_parts)

    def _get_cache_ttl(self, params: SearchParams) -> int:
        """
        Get appropriate TTL for caching based on query type.

        Args:
            params: Search parameters

        Returns:
            TTL in seconds
        """
        # Different TTLs based on query type
        if params.query and params.query.startswith('#'):
            # Hashtag searches: 1 hour
            return 3600
        elif params.sort_by == "popular":
            # Popular/trending: 15 minutes
            return 900
        else:
            # Default: 30 minutes
            return 1800

    async def _search_platform_with_fallback(
        self, provider: BaseVideoProvider, params: SearchParams
    ) -> List[VideoResult]:
        """
        Search a platform with automatic fallback to mock if needed.

        Args:
            provider: Video provider to search
            params: Search parameters

        Returns:
            List of video results or empty list on error
        """
        try:
            # First attempt with current provider
            results = await provider.search(params)

            # If production provider returned no results, try mock as fallback
            if (
                self.production_mode
                and not results
                and isinstance(provider, (MetaProvider,))
                and not isinstance(provider, MockMetaProvider)
            ):

                self._log_warning(
                    "Production provider returned no results, trying mock fallback"
                )
                mock_provider = MockMetaProvider()
                results = await mock_provider.search(params)

                if results:
                    self._log_info(f"Mock fallback returned {len(results)} results")

            return results

        except Exception as e:
            self._log_error(e, f"platform search for {provider.platform.value}")

            # For production providers, try mock fallback
            if (
                self.production_mode
                and isinstance(provider, (MetaProvider,))
                and not isinstance(provider, MockMetaProvider)
            ):

                self._log_warning(
                    f"Production provider failed: {e}, trying mock fallback"
                )
                try:
                    mock_provider = MockMetaProvider()
                    results = await mock_provider.search(params)
                    if results:
                        self._log_info(
                            f"Mock fallback returned {len(results)} results after error"
                        )
                        return results
                except Exception as fallback_error:
                    self._log_error(fallback_error, "mock fallback")

            return []

    def _get_platforms_to_search(self, requested_platform: Platform) -> List[Platform]:
        """
        Determine which platforms to search based on request.

        Args:
            requested_platform: Platform requested in search params

        Returns:
            List of platforms to search
        """
        if requested_platform == Platform.ALL:
            # Search all available platforms
            return [Platform.META]  # Meta provider handles FB+IG

        elif requested_platform == Platform.META:
            # Meta provider handles both Facebook and Instagram
            return [Platform.META]

        elif requested_platform in [Platform.INSTAGRAM, Platform.FACEBOOK]:
            # Route individual platforms through Meta provider
            return [Platform.META]

        else:
            # Unsupported platform
            self._log_warning(f"Unsupported platform requested: {requested_platform}")
            return []

    def _sort_and_limit_results(
        self, results: List[VideoResult], params: SearchParams
    ) -> List[VideoResult]:
        """
        Sort and limit search results based on parameters.

        Args:
            results: List of video results
            params: Search parameters with sorting preferences

        Returns:
            Sorted and limited list of results
        """
        if not results:
            return results

        # Sort based on preference
        if params.sort_by == "recent":
            results.sort(key=lambda x: x.created_at, reverse=True)
        elif params.sort_by == "popular":
            # Sort by engagement (likes + comments)
            results.sort(
                key=lambda x: (x.like_count or 0) + (x.comment_count or 0), reverse=True
            )
        elif params.sort_by == "relevant":
            # For now, sort by created time (relevance would require more complex scoring)
            results.sort(key=lambda x: x.created_at, reverse=True)

        # Limit results
        return results[: params.max_results]

    async def get_system_health(self) -> SystemHealth:
        """
        Get overall system health status including cache and rate limiting metrics.

        Returns:
            SystemHealth object with provider statuses and system metrics
        """
        total_providers = len(self.providers)
        healthy_providers = 0
        provider_statuses = []

        for platform, provider in self.providers.items():
            try:
                status = await provider.get_health_status()
                provider_statuses.append(status)
                if status.is_healthy:
                    healthy_providers += 1
            except Exception as e:
                self._log_error(e, f"health check for {platform.value}")
                provider_statuses.append(
                    ProviderStatus(
                        name=provider.name,
                        is_healthy=False,
                        last_check=datetime.now(),
                        error_message=str(e),
                    )
                )

        # Include cache and rate limiting statistics
        cache_stats = self.search_cache.get_stats()
        rate_limit_status = self.rate_limiter.get_status("global")

        # Add system-wide metadata to the health check
        system_metadata = {
            "cache_stats": {
                "search_results_cache": {
                    "total_entries": cache_stats.total_entries,
                    "hit_count": cache_stats.hit_count,
                    "miss_count": cache_stats.miss_count,
                    "hit_ratio": round(cache_stats.hit_ratio, 3),
                    "memory_usage_bytes": cache_stats.memory_usage_bytes
                }
            },
            "rate_limit_stats": {
                "search_requests": {
                    "requests_per_hour": rate_limit_status.requests_per_hour,
                    "current_requests": rate_limit_status.current_requests,
                    "remaining_requests": rate_limit_status.remaining_requests,
                    "is_limited": rate_limit_status.is_limited,
                    "time_until_reset_seconds": rate_limit_status.time_until_reset_seconds
                }
            },
            "system_performance": {
                "cache_hit_ratio": round(cache_stats.hit_ratio, 3),
                "rate_limit_utilization": round(rate_limit_status.current_requests / rate_limit_status.requests_per_hour, 3) if rate_limit_status.requests_per_hour > 0 else 0.0
            }
        }

        return SystemHealth(
            is_healthy=healthy_providers > 0,
            total_providers=total_providers,
            healthy_providers=healthy_providers,
            providers=provider_statuses,
            production_mode=self.production_mode,
            last_check=datetime.now(),
        )

    def get_oauth_status(self) -> Dict[str, Any]:
        """
        Get OAuth authentication status.

        Returns:
            Dictionary with OAuth status information
        """
        status = {
            "production_mode": self.production_mode,
            "oauth_configured": self.oauth_client is not None,
            "platforms_available": list(self.providers.keys()),
        }

        if self.oauth_client:
            try:
                oauth_status = self.oauth_client.get_connection_status()
                status.update(oauth_status)
            except Exception as e:
                status["oauth_error"] = str(e)

        return status

    def _log_info(self, message: str):
        """Log info message."""
        logger.info(f"SearchService: {message}")

    def _log_warning(self, message: str):
        """Log warning message."""
        logger.warning(f"SearchService: {message}")

    def _log_error(self, error: Exception, context: str = ""):
        """Log error with context."""
        error_msg = f"SearchService error"
        if context:
            error_msg += f" in {context}"
        error_msg += f": {str(error)}"
        logger.error(error_msg)
