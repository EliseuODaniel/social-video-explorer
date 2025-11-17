"""
Social Video Explorer - Core package

A comprehensive platform for searching and exploring social media video content
across multiple platforms including Instagram, Facebook, TikTok, and YouTube.
"""

__version__ = "0.1.0"
__author__ = "Social Video Explorer Team"

from .schemas import VideoResult, SearchParams, SearchResponse
from .providers import BaseVideoProvider, MetaProvider, MockMetaProvider
from .services import SearchService

__all__ = [
    "VideoResult",
    "SearchParams",
    "SearchResponse",
    "BaseVideoProvider",
    "MetaProvider",
    "MockMetaProvider",
    "SearchService",
]
