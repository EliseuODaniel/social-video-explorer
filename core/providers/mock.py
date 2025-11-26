"""
Mock provider for development and testing

This module provides mock implementations of video providers that return
sample data when real APIs are unavailable or for testing purposes.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..schemas import VideoResult, SearchParams, Platform, MediaType, ProviderStatus
from .base import BaseVideoProvider


class MockMetaProvider(BaseVideoProvider):
    """
    Mock provider for Meta platforms (Facebook + Instagram) that returns
    realistic sample data for development and testing.
    """

    def __init__(self, platform: Platform = Platform.META):
        """Initialize mock provider."""
        super().__init__(Platform.META, "Mock Meta Provider")
        self.is_healthy = True
        self._init_mock_data()

    def _init_mock_data(self):
        """Initialize mock data samples."""
        self.mock_posts = [
            {
                "id": "fb_1234567890",
                "message": "Amazing sunset at the beach today! 🌅 #sunset #beach #nature",
                "created_time": "2024-01-15T14:30:00+0000",
                "full_picture": "https://picsum.photos/400/300?random=1",
                "platform": "facebook",
            },
            {
                "id": "fb_2345678901",
                "message": "New product launch! Check out our latest innovations #tech #innovation",
                "created_time": "2024-01-14T10:15:00+0000",
                "full_picture": "https://picsum.photos/400/300?random=2",
                "platform": "facebook",
            },
            {
                "id": "ig_3456789012",
                "caption": "Morning coffee routine ☕ #coffee #morning #lifestyle",
                "timestamp": "2024-01-13T08:45:00+0000",
                "media_url": "https://picsum.photos/400/400?random=3",
                "media_type": "IMAGE",
                "like_count": 142,
                "comments_count": 23,
                "platform": "instagram",
            },
            {
                "id": "ig_4567890123",
                "caption": "Workout complete! 💪 #fitness #gym #motivation",
                "timestamp": "2024-01-12T18:20:00+0000",
                "media_url": "https://picsum.photos/400/400?random=4",
                "media_type": "IMAGE",
                "like_count": 89,
                "comments_count": 12,
                "platform": "instagram",
            },
            {
                "id": "ig_5678901234",
                "caption": "Travel Tuesday! Exploring new places ✈️ #travel #adventure #explore",
                "timestamp": "2024-01-11T16:00:00+0000",
                "media_url": "https://picsum.photos/400/400?random=5",
                "media_type": "IMAGE",
                "like_count": 234,
                "comments_count": 45,
                "platform": "instagram",
            },
            {
                "id": "fb_6789012345",
                "message": "Team building day was a success! Great energy from everyone 🎉 #team #work #corporate",
                "created_time": "2024-01-10T13:45:00+0000",
                "full_picture": "https://picsum.photos/400/300?random=6",
                "platform": "facebook",
            },
        ]

        self.mock_hashtags = [
            "travel",
            "food",
            "fitness",
            "tech",
            "nature",
            "lifestyle",
            "photography",
            "art",
            "music",
            "fashion",
            "beauty",
            "pets",
            "sunset",
            "coffee",
            "motivation",
            "adventure",
            "explore",
        ]

        self.mock_captions = [
            "Living my best life! ✨ #lifestyle #blessed",
            "Morning vibes and good energy 🌟 #morning #positive",
            "Weekend adventures are the best! 🌈 #weekend #fun",
            "Work hard, play harder 💼 #worklife #balance",
            "Grateful for the little things 🙏 #gratitude #blessed",
            "New week, new goals! 🎯 #motivation #goals",
            "Making memories that last forever 💫 #memories #life",
            "Coffee and creativity go hand in hand ☕ #coffee #creative",
            "Finding beauty in everyday moments 🌺 #beauty #mindfulness",
            "Chasing dreams and making it happen 🚀 #dreams #success",
        ]

    async def search_hashtag(
        self, hashtag: str, max_results: int = 20, media_type: MediaType = MediaType.ALL
    ) -> List[VideoResult]:
        """
        Mock hashtag search returning realistic sample data.

        Args:
            hashtag: Hashtag to search for
            max_results: Maximum results to return
            media_type: Filter by media type

        Returns:
            List of mock VideoResult objects
        """
        results = []
        hashtag = hashtag.lower()

        # Generate results that match the hashtag
        for i in range(min(max_results, 15)):  # Limit mock data
            # Mix platforms randomly
            if random.choice([True, False]):
                # Instagram post
                post = self._generate_mock_instagram_post(hashtag)
                if media_type == MediaType.ALL or post["media_type"] == media_type:
                    result = self._map_instagram_to_video_result(post)
                    results.append(result)
            else:
                # Facebook post
                post = self._generate_mock_facebook_post(hashtag)
                result = self._map_facebook_to_video_result(post)
                if result and (
                    media_type == MediaType.ALL or result.media_type == media_type
                ):
                    results.append(result)

        # Sort by creation time (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)

        self._log_info(f"Generated {len(results)} mock results for hashtag '{hashtag}'")
        return results[:max_results]

    async def search_user_content(
        self, user_id: str, max_results: int = 20
    ) -> List[VideoResult]:
        """
        Mock user content search.

        Args:
            user_id: Mock user identifier
            max_results: Maximum results to return

        Returns:
            List of mock VideoResult objects
        """
        results = []

        for i in range(min(max_results, 10)):
            if random.choice([True, False]):
                # Instagram post
                post = self._generate_mock_instagram_post(None, user_id)
                result = self._map_instagram_to_video_result(post)
                results.append(result)
            else:
                # Facebook post
                post = self._generate_mock_facebook_post(None, user_id)
                result = self._map_facebook_to_video_result(post)
                if result:
                    results.append(result)

        # Sort by creation time (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)

        self._log_info(f"Generated {len(results)} mock results for user '{user_id}'")
        return results

    def _generate_mock_instagram_post(
        self, hashtag: str = None, user_id: str = None
    ) -> Dict[str, Any]:
        """Generate a mock Instagram post."""
        post_id = f"ig_{random.randint(1000000000, 9999999999)}"
        days_ago = random.randint(0, 30)
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat() + "Z"

        if hashtag:
            caption = f"Amazing #{hashtag} post! {random.choice(self.mock_captions)}"
        else:
            caption = f"{random.choice(self.mock_captions)} #{random.choice(self.mock_hashtags)}"

        media_types = ["IMAGE", "VIDEO", "CAROUSEL_ALBUM"]
        media_type = random.choice(media_types)

        return {
            "id": post_id,
            "caption": caption,
            "timestamp": timestamp,
            "media_type": media_type,
            "media_url": f"https://picsum.photos/400/{400 if media_type == 'IMAGE' else 600}?random={random.randint(1, 1000)}",
            "permalink": f"https://instagram.com/p/{post_id}/",
            "like_count": random.randint(10, 1000),
            "comments_count": random.randint(1, 100),
            "platform": "instagram",
            "user_id": user_id or "mock_user_" + str(random.randint(1, 100)),
        }

    def _generate_mock_facebook_post(
        self, hashtag: str = None, user_id: str = None
    ) -> Dict[str, Any]:
        """Generate a mock Facebook post."""
        post_id = f"fb_{random.randint(1000000000, 9999999999)}"
        days_ago = random.randint(0, 30)
        created_time = (datetime.now() - timedelta(days=days_ago)).isoformat() + "Z"

        if hashtag:
            message = (
                f"Great content about #{hashtag}! {random.choice(self.mock_captions)}"
            )
        else:
            message = f"{random.choice(self.mock_captions)} #{random.choice(self.mock_hashtags)}"

        return {
            "id": post_id,
            "message": message,
            "created_time": created_time,
            "full_picture": f"https://picsum.photos/400/300?random={random.randint(1, 1000)}",
            "permalink_url": f"https://facebook.com/{post_id}/",
            "source": (
                f"https://video.facebook.com/{post_id}/"
                if random.choice([True, False])
                else None
            ),
            "platform": "facebook",
            "user_id": user_id or "mock_user_" + str(random.randint(1, 100)),
        }

    def _map_instagram_to_video_result(self, item: Dict[str, Any]) -> VideoResult:
        """Map mock Instagram item to VideoResult."""
        media_type_map = {
            "IMAGE": MediaType.PHOTO,
            "VIDEO": MediaType.VIDEO,
            "CAROUSEL_ALBUM": MediaType.CAROUSEL,
            "REEL": MediaType.REEL,
        }

        media_type = item.get("media_type", "IMAGE")
        mapped_type = media_type_map.get(media_type, MediaType.VIDEO)

        # Extract hashtags from caption
        caption = item.get("caption", "")
        hashtags = [
            word.lstrip("#") for word in caption.split() if word.startswith("#")
        ]

        return VideoResult(
            id=f"instagram_{item['id']}",
            title=caption[:200],
            url=item.get("permalink", ""),
            thumbnail_url=item.get("media_url"),
            created_at=datetime.fromisoformat(
                item.get("timestamp", "").replace("Z", "+00:00")
            ),
            platform=Platform.INSTAGRAM,
            media_type=mapped_type,
            like_count=item.get("like_count"),
            comment_count=item.get("comments_count"),
            hashtags=hashtags,
            raw_payload=item,
        )

    def _map_facebook_to_video_result(self, post: Dict[str, Any]) -> VideoResult:
        """Map mock Facebook post to VideoResult."""
        media_type = MediaType.VIDEO if post.get("source") else MediaType.PHOTO

        # Extract hashtags from message
        message = post.get("message", "")
        hashtags = [
            word.lstrip("#") for word in message.split() if word.startswith("#")
        ]

        return VideoResult(
            id=f"facebook_{post['id']}",
            title=message[:200],
            url=post.get("permalink_url", f"https://facebook.com/{post['id']}"),
            thumbnail_url=post.get("full_picture"),
            created_at=datetime.fromisoformat(
                post.get("created_time", "").replace("Z", "+00:00")
            ),
            platform=Platform.FACEBOOK,
            media_type=media_type,
            hashtags=hashtags,
            raw_payload=post,
        )

    async def get_health_status(self) -> ProviderStatus:
        """Return health status (always healthy for mock provider)."""
        return ProviderStatus(
            name=self.name,
            is_healthy=True,
            last_check=datetime.now(),
            response_time_ms=random.randint(10, 50),  # Mock fast response
            oauth_status="Mock mode - no authentication required",
        )
