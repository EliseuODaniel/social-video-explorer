"""Tests for search service functionality."""

import pytest

from core.services.search_service import SearchService
from core.schemas import SearchParams, VideoProvider


class TestSearchService:
    """Test SearchService functionality."""

    def test_search_service_initialization(self):
        """Test SearchService initialization."""
        service = SearchService()
        available_providers = service.get_available_providers()

        # Mock provider should always be available
        assert VideoProvider.MOCK in available_providers

        # Should have both mock and meta providers initialized
        assert len(available_providers) >= 1

    def test_get_provider_info(self):
        """Test getting provider information."""
        service = SearchService()
        info = service.get_provider_info()

        assert "total_providers" in info
        assert "available_providers" in info
        assert "provider_details" in info

        # Should have details for mock provider
        assert "mock" in info["provider_details"]
        mock_info = info["provider_details"]["mock"]
        assert mock_info["is_available"] is True
        assert mock_info["is_configured"] is True

    @pytest.mark.asyncio
    async def test_search_with_mock_provider(self):
        """Test search using mock provider."""
        service = SearchService()
        params = SearchParams(query="test videos", max_results=5)

        response = await service.search(params)

        assert response.results is not None
        assert len(response.results) <= 5  # Should not exceed max_results
        assert response.total_results == len(response.results)
        assert response.provider_used == VideoProvider.MOCK
        assert response.is_mock_mode is True

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test search with empty query raises error."""
        service = SearchService()

        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await service.search(SearchParams(query=""))

        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await service.search(SearchParams(query="   "))

    @pytest.mark.asyncio
    async def test_search_specify_provider(self):
        """Test search specifying a particular provider."""
        service = SearchService()
        params = SearchParams(
            query="test",
            max_results=3,
            provider=VideoProvider.MOCK
        )

        response = await service.search(params)

        assert response.provider_used == VideoProvider.MOCK
        assert response.is_mock_mode is True

    def test_select_provider_with_requested_available(self):
        """Test provider selection when requested provider is available."""
        service = SearchService()

        # Mock should always be available
        provider = service._select_provider(VideoProvider.MOCK)
        assert provider == VideoProvider.MOCK

    def test_select_provider_fallback_to_mock(self):
        """Test fallback to mock when requested provider not available."""
        service = SearchService()

        # If Meta is not configured, should fallback to mock
        provider = service._select_provider(VideoProvider.META)
        assert provider == VideoProvider.MOCK

    def test_select_provider_auto_selection(self):
        """Test automatic provider selection when none specified."""
        service = SearchService()

        # Should select first available provider (mock if nothing else)
        provider = service._select_provider(None)
        assert provider in [VideoProvider.MOCK]  # Should be mock

    @pytest.mark.asyncio
    async def test_search_with_meta_fallback_to_mock(self):
        """Test search fallback from Meta to mock when credentials missing."""
        service = SearchService()
        params = SearchParams(
            query="test",
            max_results=3,
            provider=VideoProvider.META  # Request Meta but no credentials
        )

        response = await service.search(params)

        # Should fallback to mock
        assert response.provider_used == VideoProvider.MOCK
        assert response.is_mock_mode is True

    @pytest.mark.asyncio
    async def test_search_max_results_limit(self):
        """Test that search respects max_results parameter."""
        service = SearchService()
        params = SearchParams(query="test", max_results=15)

        response = await service.search(params)

        # Mock provider may limit to 20, but should respect our max_results
        assert len(response.results) <= params.max_results

    def test_service_with_meta_credentials(self):
        """Test service with Meta credentials configured."""
        config = {"meta": {"access_token": "fake_token"}}
        service = SearchService(config)

        info = service.get_provider_info()
        meta_info = info["provider_details"]["meta"]

        # Should show Meta as configured (even with fake token)
        assert meta_info["is_configured"] is True