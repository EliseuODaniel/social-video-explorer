"""
Base video provider interface

This module defines the abstract interface that all video providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..schemas import VideoResult, SearchParams, Platform, MediaType, ProviderStatus


logger = logging.getLogger(__name__)


class BaseVideoProvider(ABC):
    """Abstract base class for video content providers."""

    def __init__(self, platform: Platform, name: str = None):
        """
        Initialize the provider.

        Args:
            platform: The platform this provider handles
            name: Custom provider name (defaults to platform value)
        """
        self.platform = platform
        self.name = name or f"{platform.value}_provider"
        self.is_healthy = False
        self.last_error: Optional[str] = None
        self.last_check: Optional[datetime] = None

    @abstractmethod
    async def search_hashtag(
        self, hashtag: str, max_results: int = 20, media_type: MediaType = MediaType.ALL
    ) -> List[VideoResult]:
        """
        Search for content by hashtag.

        Args:
            hashtag: Hashtag to search for (without #)
            max_results: Maximum number of results to return
            media_type: Filter by media type

        Returns:
            List of video results
        """
        pass

    @abstractmethod
    async def search_user_content(
        self, user_id: str, max_results: int = 20
    ) -> List[VideoResult]:
        """
        Search for content from a specific user.

        Args:
            user_id: Platform-specific user identifier
            max_results: Maximum number of results to return

        Returns:
            List of video results
        """
        pass

    async def search(self, params: SearchParams) -> List[VideoResult]:
        """
        Generic search method - routes to appropriate specific search method.

        Args:
            params: Search parameters

        Returns:
            List of video results
        """
        # Default implementation - providers can override for more sophisticated routing
        return await self.search_hashtag(
            hashtag=params.query,
            max_results=params.max_results,
            media_type=params.media_type,
        )

    @abstractmethod
    async def get_health_status(self) -> ProviderStatus:
        """
        Check the health and status of this provider.

        Returns:
            ProviderStatus with current health information
        """
        pass

    async def authenticate(self) -> bool:
        """
        Authenticate with the platform API if required.

        Returns:
            True if authentication successful, False otherwise
        """
        # Default implementation - many providers don't need auth
        return True

    def _map_to_video_result(
        self, item: Dict[str, Any], media_type: MediaType = MediaType.VIDEO
    ) -> VideoResult:
        """
        Helper method to map platform-specific item to VideoResult.

        Args:
            item: Raw item from platform API
            media_type: Type of media content

        Returns:
            VideoResult object
        """
        # Default implementation - providers should override this
        # with platform-specific mapping logic
        return VideoResult(
            id=f"{self.platform.value}_{item.get('id', 'unknown')}",
            title=item.get("title", item.get("caption", "Untitled")),
            url=item.get("url", ""),
            thumbnail_url=item.get("thumbnail_url"),
            created_at=item.get("created_at", datetime.now()),
            platform=self.platform,
            media_type=media_type,
            raw_payload=item,
        )

    def _log_error(self, error: Exception, context: str = ""):
        """Log error with context."""
        error_msg = f"{self.name} error"
        if context:
            error_msg += f" in {context}"
        error_msg += f": {str(error)}"

        logger.error(error_msg)
        self.last_error = str(error)
        self.is_healthy = False

    def _log_info(self, message: str):
        """Log info message."""
        logger.info(f"{self.name}: {message}")

    def _log_warning(self, message: str):
        """Log warning message."""
        logger.warning(f"{self.name}: {message}")
