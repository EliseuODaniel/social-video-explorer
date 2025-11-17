"""Integration tests and smoke tests."""

import pytest
import asyncio
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.search_service import SearchService
from core.schemas import SearchParams, VideoProvider
from core.providers.mock import MockProvider
from core.providers.meta import MetaProvider


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test complete search workflow end-to-end."""
        # Initialize service
        service = SearchService()

        # Create search parameters
        params = SearchParams(query="nature documentaries", max_results=10)

        # Perform search
        response = await service.search(params)

        # Validate response structure
        assert response.results is not None
        assert response.total_results == len(response.results)
        assert response.search_params.query == "nature documentaries"
        assert response.search_params.max_results == 10

        # Validate results
        if response.results:  # Only test if we have results
            for video in response.results:
                assert video.video_id is not None
                assert video.title is not None
                assert video.provider is not None
                assert video.url is not None
                assert video.raw_payload is not None

    @pytest.mark.asyncio
    async def test_mock_provider_integration(self):
        """Test mock provider integration specifically."""
        mock_provider = MockProvider()
        params = SearchParams(query="test integration", max_results=5)

        results = await mock_provider.search(params)

        assert len(results) == 5
        for result in results:
            assert "Test Integration" in result.title
            assert result.provider == VideoProvider.MOCK
            assert result.raw_payload["mock_data"] is True

    @pytest.mark.asyncio
    async def test_meta_provider_stub_integration(self):
        """Test Meta provider stub integration."""
        meta_provider = MetaProvider()
        params = SearchParams(query="meta test", max_results=3)

        # Should raise error for missing credentials
        from core.providers.base import ProviderError
        with pytest.raises(ProviderError):
            await meta_provider.search(params)

    @pytest.mark.asyncio
    async def test_provider_selection_and_fallback(self):
        """Test provider selection and fallback logic."""
        service = SearchService()

        # Test explicit mock selection
        params_mock = SearchParams(query="test", provider=VideoProvider.MOCK)
        response_mock = await service.search(params_mock)
        assert response_mock.provider_used == VideoProvider.MOCK

        # test meta fallback (should fallback to mock if no credentials)
        params_meta = SearchParams(query="test", provider=VideoProvider.META)
        response_meta = await service.search(params_meta)
        assert response_meta.provider_used == VideoProvider.MOCK  # Fallback

    @pytest.mark.asyncio
    async def test_service_provider_info(self):
        """Test service provider information gathering."""
        service = SearchService()
        info = service.get_provider_info()

        # Should have information about providers
        assert info["total_providers"] >= 1
        assert "mock" in info["provider_details"]
        assert "meta" in info["provider_details"]

        # Mock provider should be available
        mock_info = info["provider_details"]["mock"]
        assert mock_info["is_available"] is True

    def test_import_smoke_test(self):
        """Test that all core modules can be imported successfully."""
        # This test ensures there are no import errors in the core modules
        from core.schemas import VideoResult, SearchParams, SearchResponse
        from core.providers.base import BaseVideoProvider, ProviderCapabilities
        from core.providers.mock import MockProvider
        from core.providers.meta import MetaProvider
        from core.services.search_service import SearchService

        # Basic instantiation test
        VideoResult(
            video_id="test",
            title="Test Video",
            provider=VideoProvider.MOCK,
            url="http://example.com"
        )
        SearchParams(query="test")
        MockProvider()
        MetaProvider()
        SearchService()


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_search_parameters(self):
        """Test handling of invalid search parameters."""
        service = SearchService()

        # Empty query should raise ValueError
        with pytest.raises(ValueError):
            await service.search(SearchParams(query=""))

    @pytest.mark.asyncio
    async def test_provider_error_propagation(self):
        """Test that provider errors are properly handled."""
        service = SearchService()

        # This should not crash, but should handle errors gracefully
        try:
            response = await service.search(SearchParams(query="test", provider=VideoProvider.META))
            # If it succeeds (fallback to mock), that's fine
            assert response is not None
        except Exception as e:
            # Should be a ProviderError, not a raw exception
            from core.providers.base import ProviderError
            assert isinstance(e, ProviderError)

    def test_validation_errors(self):
        """Test Pydantic model validation errors."""
        from pydantic import ValidationError

        # Invalid VideoResult should raise ValidationError
        with pytest.raises(ValidationError):
            # Missing required fields
            from core.schemas import VideoResult
            VideoResult()

        # Invalid SearchParams should raise ValidationError
        with pytest.raises(ValidationError):
            from core.schemas import SearchParams
            SearchParams(query="", max_results=0)  # Empty query and invalid max_results