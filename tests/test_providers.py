"""Tests for video providers."""

import pytest

from core.providers.base import BaseVideoProvider, ProviderCapabilities, ProviderError
from core.providers.mock import MockProvider
from core.providers.meta import MetaProvider
from core.schemas import SearchParams, VideoProvider


class TestProviderCapabilities:
    """Test ProviderCapabilities class."""

    def test_capabilities_creation(self):
        """Test creating ProviderCapabilities."""
        caps = ProviderCapabilities(
            supports_search=True,
            supports_pagination=False,
            max_results_per_search=25,
            requires_authentication=True,
            supported_filters=["date_range", "content_type"]
        )

        assert caps.supports_search is True
        assert caps.supports_pagination is False
        assert caps.max_results_per_search == 25
        assert caps.requires_authentication is True
        assert caps.supported_filters == ["date_range", "content_type"]

    def test_capabilities_to_dict(self):
        """Test ProviderCapabilities to_dict conversion."""
        caps = ProviderCapabilities(max_results_per_search=50)
        caps_dict = caps.to_dict()

        expected_keys = [
            "supports_search", "supports_pagination",
            "max_results_per_search", "requires_authentication",
            "supported_filters"
        ]

        for key in expected_keys:
            assert key in caps_dict

        assert caps_dict["max_results_per_search"] == 50


class TestMockProvider:
    """Test MockProvider functionality."""

    @pytest.mark.asyncio
    async def test_mock_provider_search(self):
        """Test mock provider search functionality."""
        provider = MockProvider()
        params = SearchParams(query="test video", max_results=5)

        results = await provider.search(params)

        assert len(results) == 5
        assert all(isinstance(result.video_id, str) for result in results)
        assert all(result.provider == VideoProvider.MOCK for result in results)
        assert all("test video".title() in result.title for result in results)

    @pytest.mark.asyncio
    async def test_mock_provider_different_queries(self):
        """Test that different queries generate different results."""
        provider = MockProvider()

        params1 = SearchParams(query="cats", max_results=3)
        params2 = SearchParams(query="dogs", max_results=3)

        results1 = await provider.search(params1)
        results2 = await provider.search(params2)

        # Results should be different for different queries
        titles1 = [r.title for r in results1]
        titles2 = [r.title for r in results2]

        # Should not be identical (deterministic but different based on query)
        assert titles1 != titles2

    def test_mock_provider_capabilities(self):
        """Test mock provider capabilities."""
        provider = MockProvider()
        caps = provider.get_capabilities()

        assert isinstance(caps, ProviderCapabilities)
        assert caps.supports_search is True
        assert caps.requires_authentication is False
        assert caps.max_results_per_search == 50

    def test_mock_provider_availability(self):
        """Test that mock provider is always available."""
        provider = MockProvider()
        assert provider.is_available() is True


class TestMetaProvider:
    """Test MetaProvider stub functionality."""

    def test_meta_provider_creation(self):
        """Test MetaProvider creation."""
        provider = MetaProvider()
        assert provider.provider_type == VideoProvider.META

    def test_meta_provider_capabilities(self):
        """Test Meta provider capabilities."""
        provider = MetaProvider()
        caps = provider.get_capabilities()

        assert isinstance(caps, ProviderCapabilities)
        assert caps.supports_search is True
        assert caps.requires_authentication is True
        assert caps.max_results_per_search == 25

    @pytest.mark.asyncio
    async def test_meta_provider_without_credentials(self):
        """Test Meta provider without credentials raises error."""
        provider = MetaProvider()  # No config provided
        params = SearchParams(query="test")

        with pytest.raises(ProviderError) as exc_info:
            await provider.search(params)

        assert "Meta API credentials not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_meta_provider_with_credentials(self):
        """Test Meta provider with fake credentials."""
        provider = MetaProvider({"access_token": "fake_token"})
        params = SearchParams(query="test")

        # Even with fake token, should not raise credentials error
        # but should return empty results (stub implementation)
        results = await provider.search(params)
        assert results == []  # Stub returns empty list when credentials present

    def test_meta_provider_credential_validation(self):
        """Test Meta provider credential validation."""
        provider_no_creds = MetaProvider()
        provider_with_creds = MetaProvider({"access_token": "token"})

        assert not provider_no_creds._has_required_credentials()
        assert provider_with_creds._has_required_credentials()

    def test_meta_provider_config_info(self):
        """Test Meta provider configuration info."""
        provider = MetaProvider()
        info = provider.get_config_info()

        assert info["provider_type"] == "meta"
        assert info["platforms"] == ["Facebook", "Instagram"]
        assert "credential_status" in info

    def test_meta_provider_setup_instructions(self):
        """Test Meta provider setup instructions."""
        provider = MetaProvider()
        instructions = provider.get_setup_instructions()

        assert "Meta Developer Account" in instructions
        assert "META_ACCESS_TOKEN" in instructions


class TestBaseProvider:
    """Test BaseVideoProvider abstract class."""

    def test_provider_error_creation(self):
        """Test ProviderError creation."""
        error = ProviderError(
            "Test error message",
            VideoProvider.MOCK,
            original_error=Exception("Original")
        )

        assert str(error) == "[MOCK] Test error message (caused by: Exception: Original)"
        assert error.provider_type == VideoProvider.MOCK
        assert error.original_error is not None

    def test_provider_error_without_original(self):
        """Test ProviderError without original error."""
        error = ProviderError("Simple error", VideoProvider.YOUTUBE)

        assert str(error) == "[YOUTUBE] Simple error"
        assert error.original_error is None