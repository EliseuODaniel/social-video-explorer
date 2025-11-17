"""
Tests for search service implementation
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import os

from core.services.search_service import SearchService
from core.providers.mock import MockMetaProvider
from core.providers.meta import MetaProvider
from core.providers.oauth_client import MetaOAuth2Client
from core.schemas import SearchParams, Platform, MediaType, SearchResponse


class TestSearchService:
    """Test cases for SearchService."""

    def setup_method(self):
        """Set up test environment."""
        # Ensure clean environment for each test
        if "PRODUCTION_MODE" in os.environ:
            del os.environ["PRODUCTION_MODE"]

    def teardown_method(self):
        """Clean up after tests."""
        if "PRODUCTION_MODE" in os.environ:
            del os.environ["PRODUCTION_MODE"]

    def test_initialization_in_mock_mode(self):
        """Test service initialization in mock mode."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            service = SearchService()

            assert service.production_mode is False
            assert not service.oauth_client
            assert len(service.providers) > 0
            assert all(
                isinstance(p, MockMetaProvider) for p in service.providers.values()
            )

    @patch("core.providers.oauth_client.MetaOAuth2Client")
    def test_initialization_in_production_mode(self, mock_oauth_client):
        """Test service initialization in production mode."""
        # Mock successful OAuth client creation
        mock_oauth_client.return_value = Mock()

        with patch.dict(
            "os.environ",
            {
                "PRODUCTION_MODE": "true",
                "META_APP_ID": "test_id",
                "META_APP_SECRET": "test_secret",
                "META_REDIRECT_URI": "http://localhost:8501/oauth/callback",
            },
        ):
            service = SearchService()

            assert service.production_mode is True
            assert service.oauth_client is not None  # Real OAuth client created
            assert Platform.META in service.providers
            assert Platform.INSTAGRAM in service.providers
            assert Platform.FACEBOOK in service.providers
            # Check that providers are actual MetaProvider instances
            from core.providers.meta import MetaProvider
            assert isinstance(service.providers[Platform.META], MetaProvider)

    @patch("core.providers.oauth_client.MetaOAuth2Client")
    @patch("core.providers.meta.MetaProvider")
    def test_initialization_fallback_to_mock(
        self, mock_meta_provider, mock_oauth_client
    ):
        """Test fallback to mock when production initialization fails."""
        mock_oauth_client.side_effect = Exception("OAuth client init failed")

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            service = SearchService()

            # Should fall back to mock mode
            assert service.production_mode is False
            assert not service.oauth_client
            assert all(
                isinstance(p, MockMetaProvider) for p in service.providers.values()
            )

    @pytest.mark.asyncio
    async def test_search_in_mock_mode(self):
        """Test search functionality in mock mode."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            service = SearchService()

            params = SearchParams(query="travel", platform=Platform.ALL, max_results=10)

            response = await service.search(params)

            assert isinstance(response, SearchResponse)
            assert response.total_found >= 0
            assert len(response.results) <= params.max_results
            assert response.query_used == "travel"
            assert response.search_time_ms >= 0

    @pytest.mark.asyncio
    async def test_search_with_specific_platform(self):
        """Test search with specific platform filter."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            service = SearchService()

            params = SearchParams(
                query="fitness", platform=Platform.INSTAGRAM, max_results=5
            )

            response = await service.search(params)

            assert isinstance(response, SearchResponse)
            # Should return Instagram or Facebook results (MockMetaProvider returns both)
            for result in response.results:
                assert result.platform in [Platform.INSTAGRAM, Platform.FACEBOOK]

    @pytest.mark.asyncio
    async def test_search_with_media_type_filter(self):
        """Test search with media type filter."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            service = SearchService()

            params = SearchParams(
                query="test",
                platform=Platform.ALL,
                media_type=MediaType.VIDEO,
                max_results=20,
            )

            response = await service.search(params)

            # Should only return video results
            for result in response.results:
                assert result.media_type == MediaType.VIDEO

    @pytest.mark.asyncio
    async def test_search_with_sorting(self):
        """Test search with different sorting options."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            service = SearchService()

            # Test sorting by recent
            params = SearchParams(
                query="test", platform=Platform.ALL, sort_by="recent", max_results=10
            )

            response = await service.search(params)

            if len(response.results) > 1:
                # Results should be sorted by creation time (newest first)
                for i in range(len(response.results) - 1):
                    assert (
                        response.results[i].created_at
                        >= response.results[i + 1].created_at
                    )

    @pytest.mark.asyncio
    async def test_search_handles_provider_errors(self):
        """Test search handles provider errors gracefully."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):  # Use mock mode
            service = SearchService()

            # Mock _search_platform_with_fallback to raise exception directly
            original_method = service._search_platform_with_fallback
            async def failing_fallback(provider, params):
                raise Exception("Provider error")

            service._search_platform_with_fallback = failing_fallback

            params = SearchParams(
                query="test", platform=Platform.INSTAGRAM, max_results=10
            )

            response = await service.search(params)

            # Should handle error and return response with error information
            assert isinstance(response, SearchResponse)
            assert len(response.errors) > 0
            assert "Error searching" in response.errors[0]

    @pytest.mark.asyncio
    async def test_search_platform_fallback(self):
        """Test search fallback from production to mock provider."""
        # Create a mock production provider that returns empty results
        production_provider = Mock(spec=MetaProvider)
        production_provider.platform = Platform.META
        production_provider.search.return_value = []  # Empty results

        service = SearchService()
        service.production_mode = True
        service.providers[Platform.META] = production_provider

        params = SearchParams(query="test", platform=Platform.META, max_results=10)

        response = await service.search(params)

        # Should have called production provider and possibly fallback
        assert isinstance(response, SearchResponse)
        production_provider.search.assert_called_once_with(params)

    @pytest.mark.asyncio
    async def test_get_system_health(self):
        """Test system health check."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            service = SearchService()

            health = await service.get_system_health()

            assert health.total_providers > 0
            assert health.healthy_providers > 0
            assert health.is_healthy is True
            assert health.production_mode is False
            assert len(health.providers) > 0

    def test_get_oauth_status_mock_mode(self):
        """Test OAuth status in mock mode."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            service = SearchService()

            status = service.get_oauth_status()

            assert status["production_mode"] is False
            assert status["oauth_configured"] is False
            assert "platforms_available" in status

    def test_get_oauth_status_production_mode(self):
        """Test OAuth status in production mode."""
        with patch.dict(
            "os.environ",
            {
                "PRODUCTION_MODE": "true",
                "META_APP_ID": "test_id",
                "META_APP_SECRET": "test_secret",
                "META_REDIRECT_URI": "http://localhost:8501/oauth/callback",
            },
        ):
            service = SearchService()

            # Mock the OAuth client to simulate having a token
            if service.oauth_client:
                service.oauth_client._app_token = "test_token"

            status = service.get_oauth_status()

            assert status["production_mode"] is True
            assert status["oauth_configured"] is True
            # Should have app_token=True since we mocked it
            assert status["has_app_token"] is True

    def test_get_platforms_to_search_all(self):
        """Test platform selection for ALL platforms."""
        service = SearchService()
        platforms = service._get_platforms_to_search(Platform.ALL)

        assert Platform.META in platforms

    def test_get_platforms_to_search_meta(self):
        """Test platform selection for META."""
        service = SearchService()
        platforms = service._get_platforms_to_search(Platform.META)

        assert Platform.META in platforms

    def test_get_platforms_to_search_instagram(self):
        """Test platform selection for INSTAGRAM."""
        service = SearchService()
        platforms = service._get_platforms_to_search(Platform.INSTAGRAM)

        assert Platform.META in platforms

    def test_get_platforms_to_search_facebook(self):
        """Test platform selection for FACEBOOK."""
        service = SearchService()
        platforms = service._get_platforms_to_search(Platform.FACEBOOK)

        assert Platform.META in platforms

    def test_get_platforms_to_search_unsupported(self):
        """Test platform selection for unsupported platform."""
        service = SearchService()
        platforms = service._get_platforms_to_search(Platform.TIKTOK)

        assert len(platforms) == 0

    def test_sort_and_limit_results(self):
        """Test result sorting and limiting."""
        service = SearchService()

        # Create mock results
        from core.schemas import VideoResult
        from datetime import datetime, timedelta

        results = [
            VideoResult(
                id="test_1",
                title="Test 1",
                url="http://example.com/1",
                created_at=datetime.now() - timedelta(days=2),
                platform=Platform.INSTAGRAM,
                media_type=MediaType.VIDEO,
                like_count=50,
                comment_count=10,
                raw_payload={},
            ),
            VideoResult(
                id="test_2",
                title="Test 2",
                url="http://example.com/2",
                created_at=datetime.now(),
                platform=Platform.FACEBOOK,
                media_type=MediaType.PHOTO,
                like_count=100,
                comment_count=20,
                raw_payload={},
            ),
            VideoResult(
                id="test_3",
                title="Test 3",
                url="http://example.com/3",
                created_at=datetime.now() - timedelta(days=1),
                platform=Platform.INSTAGRAM,
                media_type=MediaType.VIDEO,
                like_count=25,
                comment_count=5,
                raw_payload={},
            ),
        ]

        # Test sorting by recent
        params = SearchParams(query="test", max_results=2, sort_by="recent")
        sorted_results = service._sort_and_limit_results(results, params)

        assert len(sorted_results) == 2
        # Should be sorted newest first
        assert sorted_results[0].created_at >= sorted_results[1].created_at

        # Test sorting by popularity
        params = SearchParams(query="test", max_results=2, sort_by="popular")
        sorted_results = service._sort_and_limit_results(results, params)

        assert len(sorted_results) == 2
        # Should be sorted by engagement
        total_engagement_0 = (sorted_results[0].like_count or 0) + (
            sorted_results[0].comment_count or 0
        )
        total_engagement_1 = (sorted_results[1].like_count or 0) + (
            sorted_results[1].comment_count or 0
        )
        assert total_engagement_0 >= total_engagement_1
