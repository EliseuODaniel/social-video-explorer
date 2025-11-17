"""Core Pydantic schemas for Social Video Explorer.

This module defines the fundamental data models used throughout the application
for representing video search parameters and results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator


class VideoProvider(str, Enum):
    """Supported video providers."""
    META = "meta"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    MOCK = "mock"


class VideoResult(BaseModel):
    """Normalized video result from any provider.

    This model represents a standardized video result across all platforms,
    with both normalized fields and raw payload preservation.
    """

    # Core normalized fields
    video_id: str = Field(..., description="Unique video identifier from provider")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    provider: VideoProvider = Field(..., description="Source video platform")
    url: str = Field(..., description="Direct URL to video")

    # Engagement metrics (optional, may not be available from all providers)
    view_count: Optional[int] = Field(None, description="Number of views")
    like_count: Optional[int] = Field(None, description="Number of likes")
    comment_count: Optional[int] = Field(None, description="Number of comments")
    share_count: Optional[int] = Field(None, description="Number of shares")

    # Metadata
    duration_seconds: Optional[int] = Field(None, description="Video duration in seconds")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    author: Optional[str] = Field(None, description="Video author/channel name")

    # Raw data preservation
    raw_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete raw response from provider API"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @validator('duration_seconds')
    def validate_duration(cls, v):
        """Validate duration is non-negative."""
        if v is not None and v < 0:
            raise ValueError('Duration must be non-negative')
        return v

    @validator('view_count', 'like_count', 'comment_count', 'share_count')
    def validate_counts(cls, v):
        """Validate engagement counts are non-negative."""
        if v is not None and v < 0:
            raise ValueError('Engagement counts must be non-negative')
        return v


class SearchParams(BaseModel):
    """Parameters for video search queries.

    This model defines the parameters accepted by the search service,
    with validation and sensible defaults.
    """

    query: str = Field(..., min_length=1, description="Search query string")
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )

    # Provider selection
    provider: Optional[VideoProvider] = Field(
        None,
        description="Specific provider to search (None for all available)"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True

    @validator('query')
    def validate_query(cls, v):
        """Validate search query is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()


class SearchResponse(BaseModel):
    """Response from video search operations.

    Contains search results along with metadata about the search operation.
    """

    results: List[VideoResult] = Field(default_factory=list, description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    search_params: SearchParams = Field(..., description="Parameters used for search")
    provider_used: Optional[VideoProvider] = Field(None, description="Provider that was used")
    is_mock_mode: bool = Field(False, description="Whether results are from mock provider")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True