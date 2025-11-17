"""
Pydantic schemas for Social Video Explorer

This module defines the core data structures used throughout the application
for representing search parameters, video results, and API responses.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Platform(str, Enum):
    """Supported social media platforms."""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    META = "meta"  # Combined Facebook + Instagram
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    ALL = "all"


class MediaType(str, Enum):
    """Supported media types."""

    VIDEO = "video"
    PHOTO = "photo"
    CAROUSEL = "carousel"
    REEL = "reel"
    STORY = "story"
    ALL = "all"


class SearchParams(BaseModel):
    """Parameters for video search operations."""

    query: str = Field(
        ..., min_length=1, max_length=500, description="Search query or hashtag"
    )
    platform: Platform = Field(Platform.ALL, description="Platform to search")
    media_type: MediaType = Field(MediaType.ALL, description="Media type filter")
    max_results: int = Field(
        20, ge=1, le=100, description="Maximum results per platform"
    )
    date_from: Optional[datetime] = Field(
        None, description="Filter content from this date"
    )
    date_to: Optional[datetime] = Field(
        None, description="Filter content until this date"
    )
    sort_by: str = Field("recent", description="Sort order: recent, popular, relevant")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        """Validate search query format."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        # Remove # from hashtags if present
        return v.strip().lstrip("#")

    model_config = {"use_enum_values": True}


class VideoResult(BaseModel):
    """Standardized video result from any platform."""

    id: str = Field(..., description="Unique identifier with platform prefix")
    title: str = Field(..., max_length=200, description="Content title or caption")
    url: HttpUrl = Field(..., description="URL to original content")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="URL to thumbnail image")
    created_at: datetime = Field(..., description="Content creation timestamp")
    platform: Platform = Field(..., description="Source platform")
    media_type: MediaType = Field(..., description="Type of media content")
    duration: Optional[int] = Field(None, description="Video duration in seconds")
    view_count: Optional[int] = Field(None, description="Number of views")
    like_count: Optional[int] = Field(None, description="Number of likes")
    comment_count: Optional[int] = Field(None, description="Number of comments")
    hashtags: List[str] = Field(default_factory=list, description="Associated hashtags")
    raw_payload: Dict = Field(..., description="Original API response for debugging")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v, info):
        """Ensure ID has platform prefix."""
        if "platform" in info.data and info.data["platform"]:
            platform = info.data["platform"]
            if not v.startswith(f"{platform.value}_"):
                return f"{platform.value}_{v}"
        return v

    model_config = {"use_enum_values": True}


class SearchResponse(BaseModel):
    """Response wrapper for search operations."""

    results: List[VideoResult] = Field(
        default_factory=list, description="Search results"
    )
    total_found: int = Field(0, description="Total results found (may exceed returned)")
    search_time_ms: int = Field(0, description="Search duration in milliseconds")
    platforms_searched: List[Platform] = Field(
        default_factory=list, description="Platforms included"
    )
    has_more: bool = Field(False, description="Whether more results are available")
    query_used: str = Field(..., description="The actual query that was executed")
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )

    model_config = {"use_enum_values": True}


class ProviderStatus(BaseModel):
    """Status information for a provider."""

    name: str = Field(..., description="Provider name")
    is_healthy: bool = Field(False, description="Provider health status")
    last_check: datetime = Field(
        default_factory=datetime.now, description="Last health check"
    )
    error_message: Optional[str] = Field(None, description="Last error if unhealthy")
    response_time_ms: Optional[int] = Field(None, description="Last response time")
    rate_limit_remaining: Optional[int] = Field(
        None, description="Remaining API calls if applicable"
    )
    oauth_status: Optional[str] = Field(None, description="OAuth authentication status")


class SystemHealth(BaseModel):
    """Overall system health information."""

    is_healthy: bool = Field(False, description="Overall system health")
    total_providers: int = Field(0, description="Total configured providers")
    healthy_providers: int = Field(0, description="Number of healthy providers")
    providers: List[ProviderStatus] = Field(
        default_factory=list, description="Individual provider status"
    )
    production_mode: bool = Field(
        False, description="Whether production APIs are enabled"
    )
    last_check: datetime = Field(
        default_factory=datetime.now, description="Last system health check"
    )
