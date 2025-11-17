"""Tests for core Pydantic schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from core.schemas import VideoResult, SearchParams, SearchResponse, VideoProvider


class TestVideoResult:
    """Test VideoResult schema validation."""

    def test_valid_video_result_creation(self):
        """Test creating a valid VideoResult."""
        video = VideoResult(
            video_id="test_123",
            title="Test Video",
            provider=VideoProvider.MOCK,
            url="https://example.com/video/test_123"
        )

        assert video.video_id == "test_123"
        assert video.title == "Test Video"
        assert video.provider == VideoProvider.MOCK
        assert video.url == "https://example.com/video/test_123"

    def test_video_result_with_optional_fields(self):
        """Test VideoResult with all optional fields."""
        video = VideoResult(
            video_id="test_456",
            title="Complete Video",
            description="A complete video description",
            thumbnail_url="https://example.com/thumb.jpg",
            provider=VideoProvider.YOUTUBE,
            url="https://youtube.com/watch?v=test_456",
            view_count=1000,
            like_count=100,
            comment_count=10,
            duration_seconds=300,
            published_at=datetime.now(),
            author="Test Channel",
            raw_payload={"api_response": "data"}
        )

        assert video.view_count == 1000
        assert video.like_count == 100
        assert video.duration_seconds == 300
        assert video.author == "Test Channel"

    def test_negative_duration_validation(self):
        """Test that negative duration raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            VideoResult(
                video_id="test_789",
                title="Invalid Video",
                provider=VideoProvider.MOCK,
                url="https://example.com/video/test_789",
                duration_seconds=-10  # Invalid negative duration
            )

        assert "Duration must be non-negative" in str(exc_info.value)

    def test_negative_count_validation(self):
        """Test that negative engagement counts raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            VideoResult(
                video_id="test_abc",
                title="Invalid Video",
                provider=VideoProvider.MOCK,
                url="https://example.com/video/test_abc",
                view_count=-5  # Invalid negative count
            )

        assert "Engagement counts must be non-negative" in str(exc_info.value)


class TestSearchParams:
    """Test SearchParams schema validation."""

    def test_valid_search_params(self):
        """Test creating valid SearchParams."""
        params = SearchParams(query="test query", max_results=20)

        assert params.query == "test query"
        assert params.max_results == 20

    def test_default_max_results(self):
        """Test default max_results value."""
        params = SearchParams(query="test")

        assert params.max_results == 10

    def test_max_results_validation(self):
        """Test max_results boundary validation."""
        # Valid boundaries
        params_min = SearchParams(query="test", max_results=1)
        params_max = SearchParams(query="test", max_results=50)

        assert params_min.max_results == 1
        assert params_max.max_results == 50

        # Invalid: too low
        with pytest.raises(ValidationError):
            SearchParams(query="test", max_results=0)

        # Invalid: too high
        with pytest.raises(ValidationError):
            SearchParams(query="test", max_results=51)

    def test_empty_query_validation(self):
        """Test that empty query raises validation error."""
        with pytest.raises(ValidationError):
            SearchParams(query="")

        with pytest.raises(ValidationError):
            SearchParams(query="   ")  # Whitespace only

    def test_query_whitespace_trim(self):
        """Test that query whitespace is trimmed."""
        params = SearchParams(query="  test query  ")
        assert params.query == "test query"


class TestSearchResponse:
    """Test SearchResponse schema."""

    def test_search_response_creation(self):
        """Test creating a valid SearchResponse."""
        params = SearchParams(query="test")
        video = VideoResult(
            video_id="test_1",
            title="Test Video",
            provider=VideoProvider.MOCK,
            url="https://example.com/test_1"
        )

        response = SearchResponse(
            results=[video],
            total_results=1,
            search_params=params,
            provider_used=VideoProvider.MOCK,
            is_mock_mode=True
        )

        assert len(response.results) == 1
        assert response.total_results == 1
        assert response.provider_used == VideoProvider.MOCK
        assert response.is_mock_mode is True

    def test_empty_search_response(self):
        """Test SearchResponse with no results."""
        params = SearchParams(query="nonexistent")
        response = SearchResponse(
            results=[],
            total_results=0,
            search_params=params
        )

        assert response.results == []
        assert response.total_results == 0
        assert response.provider_used is None
        assert response.is_mock_mode is False