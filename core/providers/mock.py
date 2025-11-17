"""Mock video provider for demonstration and testing.

This module implements a mock provider that generates realistic sample video data
for demonstration purposes when real API credentials are not available.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .base import BaseVideoProvider, ProviderCapabilities
from ..schemas import SearchParams, VideoResult, VideoProvider


class MockProvider(BaseVideoProvider):
    """Mock video provider for demonstration purposes.

    Generates realistic sample video data to demonstrate the application
    functionality without requiring real API credentials.
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        """Initialize mock provider."""
        super().__init__(config)
        self._provider_type = VideoProvider.MOCK

        # Sample data for generating mock videos
        self.sample_titles = [
            "Amazing Nature Documentary",
            "Funny Cat Compilation 2024",
            "How to Cook Perfect Pasta",
            "Tech Review: Latest Smartphone",
            "Travel Vlog: Hidden Beach Paradise",
            "Fitness Motivation - Morning Workout",
            "Gaming Highlights - Epic Moments",
            "DIY Home Improvement Project",
            "Science Explained: Black Holes",
            "Music Video: Indie Artist Showcase"
        ]

        self.sample_authors = [
            "Nature Channel",
            "Pet Lovers United",
            "Cooking Masterclass",
            "Tech Insider",
            "Wanderlust Travel",
            "Fitness Guru",
            "Pro Gamer TV",
            "DIY Expert",
            "Science Daily",
            "Indie Music Label"
        ]

    @property
    def provider_type(self) -> VideoProvider:
        """Return the provider type."""
        return self._provider_type

    def get_capabilities(self) -> ProviderCapabilities:
        """Return mock provider capabilities.

        Returns:
            ProviderCapabilities object describing what this provider can do
        """
        return ProviderCapabilities(
            supports_search=True,
            supports_pagination=False,
            max_results_per_search=50,
            requires_authentication=False,
            supported_filters=["date_range", "duration", "content_type"]
        )

    async def search(self, params: SearchParams) -> List[VideoResult]:
        """Generate mock search results.

        Args:
            params: Search parameters

        Returns:
            List of mock VideoResult objects
        """
        num_results = min(params.max_results, 20)  # Limit mock data to 20 items
        results = []

        for i in range(num_results):
            # Generate deterministic but varied data based on query and index
            seed = hash(params.query + str(i))
            random.seed(seed)

            result = VideoResult(
                video_id=f"mock_video_{i}_{hash(params.query) % 10000}",
                title=f"{params.query.title()}: {random.choice(self.sample_titles)}",
                description=f"This is a mock video result for the search query '{params.query}'. "
                           f"Generated sample content for demonstration purposes.",
                thumbnail_url=f"https://picsum.photos/320/180?random={seed}",
                provider=self.provider_type,
                url=f"https://mock-video-platform.com/video/{i}",
                view_count=random.randint(1000, 1000000),
                like_count=random.randint(100, 50000),
                comment_count=random.randint(10, 5000),
                share_count=random.randint(5, 1000),
                duration_seconds=random.randint(30, 1800),  # 30 seconds to 30 minutes
                published_at=datetime.now() - timedelta(days=random.randint(1, 365)),
                author=random.choice(self.sample_authors),
                raw_payload={
                    "mock_data": True,
                    "search_query": params.query,
                    "generated_at": datetime.now().isoformat(),
                    "seed": seed,
                    "provider": "mock"
                }
            )
            results.append(result)

        return results

    def get_config_info(self) -> Dict[str, Any]:
        """Get mock provider configuration information.

        Returns:
            Dictionary with configuration information
        """
        info = super().get_config_info()
        info.update({
            "purpose": "Demo and testing without real API credentials",
            "data_source": "Generated sample data",
            "auth_required": False,
            "rate_limits": "None (mock provider)",
            "data_freshness": "Real-time generated"
        })
        return info