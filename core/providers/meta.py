"""
Meta provider implementation for Facebook and Instagram

This module implements real API integration with Facebook Graph API and
Instagram Basic Display API using the OAuth2 client.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

import requests
from ..schemas import VideoResult, SearchParams, Platform, MediaType, ProviderStatus
from .base import BaseVideoProvider
from .oauth_client import MetaOAuth2Client, MetaOAuthError

logger = logging.getLogger(__name__)


class MetaAPIError(Exception):
    """Custom exception for Meta API operations."""

    pass


class MetaProvider(BaseVideoProvider):
    """
    Provider for Meta platforms (Facebook + Instagram) with real API integration.
    """

    def __init__(self, oauth_client: MetaOAuth2Client):
        """
        Initialize Meta provider.

        Args:
            oauth_client: Authenticated OAuth2 client
        """
        super().__init__(Platform.META, "Meta Provider")
        self.oauth_client = oauth_client
        self.production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"

        # API configuration
        self.graph_api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"
        self.instagram_base_url = (
            f"https://graph.instagram.com/{self.graph_api_version}"
        )

        # Request timeout and retry configuration
        self.timeout = 30
        self.max_retries = 3

        self._log_info(
            f"Initialized in {'production' if self.production_mode else 'mock'} mode"
        )

    async def search_hashtag(
        self, hashtag: str, max_results: int = 20, media_type: MediaType = MediaType.ALL
    ) -> List[VideoResult]:
        """
        Search Instagram content by hashtag.

        Args:
            hashtag: Hashtag to search for (without #)
            max_results: Maximum results to return
            media_type: Filter by media type

        Returns:
            List of VideoResult objects
        """
        if not self.production_mode:
            self._log_warning("Production mode disabled, skipping real search")
            return []

        results = []

        try:
            # Instagram hashtag search requires an Instagram Business Account
            # For MVP, we'll use a simplified approach
            results.extend(
                await self._search_instagram_hashtag(hashtag, max_results, media_type)
            )

            # Also search Facebook for hashtag content
            results.extend(
                await self._search_facebook_hashtag(
                    hashtag, max_results - len(results), media_type
                )
            )

            self._log_info(f"Found {len(results)} results for hashtag '{hashtag}'")
            return results[:max_results]

        except Exception as e:
            self._log_error(e, f"hashtag search for '{hashtag}'")
            raise MetaAPIError(f"Hashtag search failed: {e}")

    async def _search_instagram_hashtag(
        self, hashtag: str, max_results: int, media_type: MediaType
    ) -> List[VideoResult]:
        """Search Instagram hashtag content."""
        try:
            app_token = self.oauth_client.get_app_token()

            # First, get the hashtag ID
            hashtag_url = f"{self.base_url}/ig_hashtag_search"
            hashtag_params = {
                "user_id": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "me"),
                "q": hashtag,
                "access_token": app_token,
            }

            response = requests.get(
                hashtag_url, params=hashtag_params, timeout=self.timeout
            )
            response.raise_for_status()

            hashtag_data = response.json()
            hashtags = hashtag_data.get("data", [])

            if not hashtags:
                self._log_warning(f"Instagram hashtag '{hashtag}' not found")
                return []

            hashtag_id = hashtags[0]["id"]
            results = []

            # Get recent media for this hashtag
            media_url = f"{self.base_url}/{hashtag_id}/recent_media"
            media_params = {
                "user_id": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "me"),
                "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                "limit": min(max_results, 50),
                "access_token": app_token,
            }

            media_response = requests.get(
                media_url, params=media_params, timeout=self.timeout
            )
            media_response.raise_for_status()

            media_data = media_response.json()
            media_items = media_data.get("data", [])

            for item in media_items:
                # Filter by media type if specified
                item_media_type = self._map_instagram_media_type(
                    item.get("media_type", "photo")
                )
                if media_type != MediaType.ALL and item_media_type != media_type:
                    continue

                video_result = self._map_instagram_to_video_result(item)
                results.append(video_result)

            self._log_info(f"Instagram hashtag search returned {len(results)} results")
            return results

        except requests.RequestException as e:
            self._log_error(e, "Instagram hashtag search")
            return []

    async def _search_facebook_hashtag(
        self, hashtag: str, max_results: int, media_type: MediaType
    ) -> List[VideoResult]:
        """Search Facebook hashtag content."""
        try:
            app_token = self.oauth_client.get_app_token()

            # Facebook hashtag search through public posts
            search_url = f"{self.base_url}/search"
            search_params = {
                "q": f"#{hashtag}",
                "type": "post",
                "fields": "id,message,created_time,full_picture,permalink_url,source",
                "limit": min(max_results, 50),
                "access_token": app_token,
            }

            response = requests.get(
                search_url, params=search_params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            posts = data.get("data", [])
            results = []

            for post in posts:
                # Check if post contains media
                if not (post.get("full_picture") or post.get("source")):
                    continue

                video_result = self._map_facebook_to_video_result(post)
                if video_result:
                    results.append(video_result)

            self._log_info(f"Facebook hashtag search returned {len(results)} results")
            return results

        except requests.RequestException as e:
            self._log_error(e, "Facebook hashtag search")
            return []

    async def search_user_content(
        self, user_id: str, max_results: int = 20
    ) -> List[VideoResult]:
        """
        Search for content from a specific user.

        Args:
            user_id: Platform-specific user identifier
            max_results: Maximum results to return

        Returns:
            List of VideoResult objects
        """
        if not self.production_mode:
            return []

        results = []

        try:
            # Try Instagram first
            results.extend(await self._search_instagram_user(user_id, max_results))

            # Then try Facebook if we still need more results
            if len(results) < max_results:
                results.extend(
                    await self._search_facebook_user(
                        user_id, max_results - len(results)
                    )
                )

            return results[:max_results]

        except Exception as e:
            self._log_error(e, f"user content search for '{user_id}'")
            return []

    async def _search_instagram_user(
        self, user_id: str, max_results: int
    ) -> List[VideoResult]:
        """Search Instagram user content."""
        try:
            user_token = self.oauth_client.get_user_token(user_id)
            if not user_token:
                app_token = self.oauth_client.get_app_token()
            else:
                app_token = user_token

            media_url = f"{self.instagram_base_url}/me/media"
            media_params = {
                "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                "limit": min(max_results, 50),
                "access_token": app_token,
            }

            response = requests.get(
                media_url, params=media_params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            media_items = data.get("data", [])

            results = []
            for item in media_items:
                video_result = self._map_instagram_to_video_result(item)
                results.append(video_result)

            return results

        except requests.RequestException as e:
            self._log_error(e, "Instagram user search")
            return []

    async def _search_facebook_user(
        self, user_id: str, max_results: int
    ) -> List[VideoResult]:
        """Search Facebook user content."""
        try:
            app_token = self.oauth_client.get_app_token()

            posts_url = f"{self.base_url}/{user_id}/posts"
            posts_params = {
                "fields": "id,message,created_time,full_picture,permalink_url,source",
                "limit": min(max_results, 50),
                "access_token": app_token,
            }

            response = requests.get(
                posts_url, params=posts_params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            posts = data.get("data", [])

            results = []
            for post in posts:
                if post.get("full_picture") or post.get("source"):
                    video_result = self._map_facebook_to_video_result(post)
                    if video_result:
                        results.append(video_result)

            return results

        except requests.RequestException as e:
            self._log_error(e, "Facebook user search")
            return []

    def _map_instagram_to_video_result(self, item: Dict[str, Any]) -> VideoResult:
        """Map Instagram media item to VideoResult."""
        media_type = self._map_instagram_media_type(item.get("media_type", "photo"))

        return VideoResult(
            id=f"instagram_{item['id']}",
            title=item.get("caption", "Instagram Post")[:200],
            url=item.get("permalink", ""),
            thumbnail_url=item.get("media_url"),
            created_at=datetime.fromisoformat(
                item.get("timestamp", "").replace("Z", "+00:00")
            ),
            platform=Platform.INSTAGRAM,
            media_type=media_type,
            like_count=item.get("like_count"),
            comment_count=item.get("comments_count"),
            raw_payload=item,
        )

    def _map_facebook_to_video_result(
        self, post: Dict[str, Any]
    ) -> Optional[VideoResult]:
        """Map Facebook post to VideoResult."""
        if not (post.get("full_picture") or post.get("source")):
            return None

        media_type = MediaType.VIDEO if post.get("source") else MediaType.PHOTO

        return VideoResult(
            id=f"facebook_{post['id']}",
            title=post.get("message", "Facebook Post")[:200],
            url=post.get("permalink_url", f"https://facebook.com/{post['id']}"),
            thumbnail_url=post.get("full_picture"),
            created_at=datetime.fromisoformat(
                post.get("created_time", "").replace("Z", "+00:00")
            ),
            platform=Platform.FACEBOOK,
            media_type=media_type,
            raw_payload=post,
        )

    def _map_instagram_media_type(self, media_type: str) -> MediaType:
        """Map Instagram media type to our MediaType enum."""
        mapping = {
            "IMAGE": MediaType.PHOTO,
            "VIDEO": MediaType.VIDEO,
            "CAROUSEL_ALBUM": MediaType.CAROUSEL,
            "REEL": MediaType.REEL,
        }
        return mapping.get(media_type.upper(), MediaType.VIDEO)

    async def get_health_status(self) -> ProviderStatus:
        """Check provider health and connection status."""
        start_time = datetime.now()
        is_healthy = True
        error_message = None
        oauth_status = None

        try:
            # Check OAuth connection status
            oauth_status_data = self.oauth_client.get_connection_status()
            oauth_status = json.dumps(oauth_status_data)

            # Test API connectivity
            if self.production_mode and oauth_status_data.get("has_app_token"):
                app_token = self.oauth_client.get_app_token()

                # Test with a simple API call
                test_url = f"{self.base_url}/me"
                params = {"access_token": app_token}

                response = requests.get(test_url, params=params, timeout=10)
                if response.status_code == 200:
                    self.is_healthy = True
                    oauth_status_data["app_token_valid"] = True
                else:
                    is_healthy = False
                    error_message = f"API test failed: {response.status_code}"
                    self.is_healthy = False

        except Exception as e:
            is_healthy = False
            error_message = str(e)
            self.is_healthy = False

        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return ProviderStatus(
            name=self.name,
            is_healthy=is_healthy,
            last_check=datetime.now(),
            error_message=error_message,
            response_time_ms=int(response_time),
            oauth_status=oauth_status,
            rate_limit_remaining=None,  # Meta doesn't provide this in simple responses
        )
