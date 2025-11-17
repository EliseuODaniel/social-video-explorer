"""
Tests for video provider implementations
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from core.providers.meta import MetaProvider, MetaAPIError
from core.providers.mock import MockMetaProvider
from core.providers.oauth_client import MetaOAuth2Client, MetaOAuthError
from core.schemas import Platform, MediaType, SearchParams


class TestMockMetaProvider:
    """Test cases for MockMetaProvider."""

    def setup_method(self):
        """Set up test environment."""
        self.provider = MockMetaProvider()

    @pytest.mark.asyncio
    async def test_search_hashtag_returns_results(self):
        """Test hashtag search returns mock results."""
        results = await self.provider.search_hashtag("travel", max_results=10)

        assert len(results) > 0
        assert len(results) <= 10
        for result in results:
            assert result.platform in [Platform.INSTAGRAM, Platform.FACEBOOK]
            assert result.id.startswith(("instagram_", "facebook_"))
            assert (
                "travel" in result.title.lower()
                or "travel" in str(result.hashtags).lower()
            )

    @pytest.mark.asyncio
    async def test_search_hashtag_with_media_type_filter(self):
        """Test hashtag search with media type filter."""
        results = await self.provider.search_hashtag(
            "test", max_results=20, media_type=MediaType.VIDEO
        )

        for result in results:
            assert result.media_type == MediaType.VIDEO

    @pytest.mark.asyncio
    async def test_search_user_content_returns_results(self):
        """Test user content search returns mock results."""
        results = await self.provider.search_user_content("test_user", max_results=5)

        assert len(results) > 0
        assert len(results) <= 5
        for result in results:
            assert result.platform in [Platform.INSTAGRAM, Platform.FACEBOOK]

    @pytest.mark.asyncio
    async def test_get_health_status(self):
        """Test health status always returns healthy for mock provider."""
        status = await self.provider.get_health_status()

        assert status.name == "Mock Meta Provider"
        assert status.is_healthy is True
        assert status.response_time_ms is not None
        assert "Mock mode" in status.oauth_status


class TestMetaProvider:
    """Test cases for MetaProvider."""

    def setup_method(self):
        """Set up test environment."""
        self.mock_oauth_client = Mock(spec=MetaOAuth2Client)
        self.provider = MetaProvider(self.mock_oauth_client)

    @pytest.mark.asyncio
    async def test_search_hashtag_in_mock_mode(self):
        """Test hashtag search in mock mode returns no results."""
        # Set production mode to False
        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            provider = MetaProvider(self.mock_oauth_client)
            results = await provider.search_hashtag("test")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_hashtag_production_mode_success(self):
        """Test successful hashtag search in production mode."""
        # Set up mock OAuth client
        self.mock_oauth_client.get_app_token.return_value = "test_token"

        # Mock Instagram API response
        mock_hashtag_response = {"data": [{"id": "hashtag_123"}]}

        mock_media_response = {
            "data": [
                {
                    "id": "media_1",
                    "caption": "Test travel post #travel",
                    "media_type": "IMAGE",
                    "media_url": "https://example.com/image.jpg",
                    "permalink": "https://instagram.com/p/test1",
                    "timestamp": "2024-01-15T10:00:00+0000",
                    "like_count": 100,
                    "comments_count": 20,
                }
            ]
        }

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            with patch("requests.get") as mock_get:
                # Configure mock responses
                mock_get.return_value.json.side_effect = [
                    mock_hashtag_response,
                    mock_media_response,
                    {"data": []},  # Facebook response
                ]
                mock_get.return_value.raise_for_status.return_value = None

                provider = MetaProvider(self.mock_oauth_client)
                results = await provider.search_hashtag("travel", max_results=10)

                assert len(results) == 1
                result = results[0]
                assert result.platform == Platform.INSTAGRAM
                assert result.id == "instagram_media_1"
                assert "travel" in result.title

    @pytest.mark.asyncio
    async def test_search_user_content_production_mode(self):
        """Test user content search in production mode."""
        # Set up mock OAuth client
        self.mock_oauth_client.get_user_token.return_value = "user_token"
        self.mock_oauth_client.get_app_token.return_value = "app_token"

        # Mock API response
        mock_media_response = {
            "data": [
                {
                    "id": "user_media_1",
                    "caption": "User post #lifestyle",
                    "media_type": "VIDEO",
                    "media_url": "https://example.com/video.mp4",
                    "permalink": "https://instagram.com/p/user1",
                    "timestamp": "2024-01-14T15:30:00+0000",
                    "like_count": 250,
                    "comments_count": 45,
                }
            ]
        }

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.json.return_value = mock_media_response
                mock_get.return_value.raise_for_status.return_value = None

                provider = MetaProvider(self.mock_oauth_client)
                results = await provider.search_user_content("user_123", max_results=10)

                assert len(results) == 1
                result = results[0]
                assert result.platform == Platform.INSTAGRAM
                assert result.media_type == MediaType.VIDEO

    @pytest.mark.asyncio
    async def test_search_handles_api_errors(self):
        """Test search handles API errors gracefully."""
        # Set up mock OAuth client
        self.mock_oauth_client.get_app_token.return_value = "test_token"

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            # Force a higher-level exception by mocking the OAuth client to fail
            self.mock_oauth_client.get_app_token.side_effect = Exception("OAuth client error")

            provider = MetaProvider(self.mock_oauth_client)

            with pytest.raises(MetaAPIError, match="Hashtag search failed"):
                await provider.search_hashtag("test")

    @pytest.mark.asyncio
    async def test_get_health_status_production_healthy(self):
        """Test health status in production mode when healthy."""
        # Set up mock OAuth client
        self.mock_oauth_client.get_connection_status.return_value = {
            "has_app_token": True,
            "app_token_valid": True,
        }
        self.mock_oauth_client.get_app_token.return_value = "test_token"

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            with patch("requests.get") as mock_get:
                # Mock successful API test
                mock_response = Mock()
                mock_response.status_code = 200
                mock_get.return_value = mock_response

                provider = MetaProvider(self.mock_oauth_client)
                status = await provider.get_health_status()

                assert status.is_healthy is True
                assert status.response_time_ms is not None
                assert "app_token_valid" in status.oauth_status

    @pytest.mark.asyncio
    async def test_get_health_status_production_unhealthy(self):
        """Test health status in production mode when unhealthy."""
        # Set up mock OAuth client with invalid token
        self.mock_oauth_client.get_connection_status.return_value = {
            "has_app_token": True,  # Has token but it's invalid
            "app_token_valid": False,
        }
        self.mock_oauth_client.get_app_token.return_value = "invalid_token"

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            with patch("requests.get") as mock_get:
                # Mock API failure (401 or similar)
                import requests
                mock_response = Mock()
                mock_response.status_code = 401
                mock_get.return_value = mock_response

                provider = MetaProvider(self.mock_oauth_client)
                status = await provider.get_health_status()

                # Should be unhealthy due to API test failure
                assert status.is_healthy is False
                assert "API test failed" in status.error_message

    @pytest.mark.asyncio
    async def test_get_health_status_mock_mode(self):
        """Test health status in mock mode."""
        # Set up mock OAuth client to avoid JSON serialization issues
        self.mock_oauth_client.get_connection_status.return_value = {
            "has_app_token": False,
            "app_token_valid": False,
        }

        with patch.dict("os.environ", {"PRODUCTION_MODE": "false"}):
            provider = MetaProvider(self.mock_oauth_client)
            status = await provider.get_health_status()

            assert status.is_healthy is True
            assert status.oauth_status is not None

    def test_map_instagram_to_video_result(self):
        """Test Instagram item mapping to VideoResult."""
        instagram_item = {
            "id": "ig_test123",
            "caption": "Test post #test",
            "timestamp": "2024-01-15T10:00:00+0000",
            "media_type": "IMAGE",
            "media_url": "https://example.com/image.jpg",
            "permalink": "https://instagram.com/p/test",
            "like_count": 100,
            "comments_count": 20,
        }

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            provider = MetaProvider(self.mock_oauth_client)
            result = provider._map_instagram_to_video_result(instagram_item)

            assert result.id == "instagram_ig_test123"
            assert result.platform == Platform.INSTAGRAM
            assert result.media_type == MediaType.PHOTO
            assert result.title == "Test post #test"
            assert result.like_count == 100

    def test_map_facebook_to_video_result(self):
        """Test Facebook post mapping to VideoResult."""
        facebook_post = {
            "id": "fb_test456",
            "message": "Test Facebook post #facebook",
            "created_time": "2024-01-15T10:00:00+0000",
            "full_picture": "https://example.com/photo.jpg",
            "permalink_url": "https://facebook.com/post/test",
        }

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            provider = MetaProvider(self.mock_oauth_client)
            result = provider._map_facebook_to_video_result(facebook_post)

            assert result.id == "facebook_fb_test456"
            assert result.platform == Platform.FACEBOOK
            assert result.media_type == MediaType.PHOTO
            assert result.title == "Test Facebook post #facebook"

    def test_map_facebook_to_video_result_no_media(self):
        """Test Facebook post mapping returns None for posts without media."""
        facebook_post = {
            "id": "fb_test789",
            "message": "Text only post",
            "created_time": "2024-01-15T10:00:00+0000",
            # No media URLs
        }

        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            provider = MetaProvider(self.mock_oauth_client)
            result = provider._map_facebook_to_video_result(facebook_post)

            assert result is None

    def test_map_instagram_media_type(self):
        """Test Instagram media type mapping."""
        with patch.dict("os.environ", {"PRODUCTION_MODE": "true"}):
            provider = MetaProvider(self.mock_oauth_client)

            assert provider._map_instagram_media_type("IMAGE") == MediaType.PHOTO
            assert provider._map_instagram_media_type("VIDEO") == MediaType.VIDEO
            assert (
                provider._map_instagram_media_type("CAROUSEL_ALBUM")
                == MediaType.CAROUSEL
            )
            assert provider._map_instagram_media_type("REEL") == MediaType.REEL
            assert provider._map_instagram_media_type("UNKNOWN") == MediaType.VIDEO
