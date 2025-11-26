"""
OAuth2 client for Meta platforms (Facebook + Instagram)

This module handles OAuth2 authentication with Facebook Graph API and
Instagram Basic Display API using a single app token approach.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class MetaOAuthError(Exception):
    """Custom exception for Meta OAuth operations."""

    pass


class MetaOAuth2Client:
    """
    OAuth2 client for Meta platforms supporting both Facebook Graph API
    and Instagram Basic Display API with unified token management.
    """

    def __init__(self):
        """Initialize OAuth2 client with environment variables."""
        load_dotenv()

        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")
        self.redirect_uri = os.getenv(
            "META_REDIRECT_URI", "http://localhost:8501/oauth/callback"
        )

        # API versions
        self.graph_api_version = "v18.0"
        self.instagram_api_version = "v18.0"

        # Token storage
        self._app_token: Optional[str] = None
        self._app_token_expires: Optional[datetime] = None
        self._user_tokens: Dict[str, Dict[str, Any]] = {}

        # Base URLs
        self.graph_base_url = "https://graph.facebook.com"
        self.instagram_base_url = "https://graph.instagram.com"

        self._validate_credentials()

    def _validate_credentials(self):
        """Validate required credentials are present."""
        if not self.app_id or not self.app_secret:
            raise MetaOAuthError(
                "META_APP_ID and META_APP_SECRET environment variables are required"
            )
        logger.info(f"OAuth client initialized for app ID: {self.app_id}")

    def get_app_token(self, force_refresh: bool = False) -> str:
        """
        Get Facebook App Token for server-to-server requests.

        Args:
            force_refresh: Force token refresh even if not expired

        Returns:
            App access token
        """
        if (
            not force_refresh
            and self._app_token
            and self._app_token_expires
            and datetime.now() < self._app_token_expires
        ):
            return self._app_token

        try:
            url = f"{self.graph_base_url}/{self.graph_api_version}/oauth/access_token"
            params = {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "grant_type": "client_credentials",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            token = data.get("access_token")

            if not token:
                raise MetaOAuthError("No access token received from Meta API")

            # App tokens don't expire, but we'll cache them for 1 hour
            self._app_token = token
            self._app_token_expires = datetime.now() + timedelta(hours=1)

            logger.info("Successfully obtained Facebook app token")
            return token

        except requests.RequestException as e:
            logger.error(f"Failed to get app token: {e}")
            raise MetaOAuthError(f"Failed to obtain app token: {e}")

    def get_authorization_url(self, scopes: list = None) -> str:
        """
        Generate OAuth authorization URL for user authentication.

        Args:
            scopes: List of OAuth permissions requested

        Returns:
            Authorization URL for user to visit
        """
        if scopes is None:
            # Default scopes for Facebook + Instagram
            scopes = [
                "pages_read_engagement",
                "instagram_basic",
                "instagram_content_publish",
                "pages_show_list",
            ]

        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": ",".join(scopes),
            "response_type": "code",
        }

        url = f"{self.graph_base_url}/{self.graph_api_version}/dialog/oauth?{urlencode(params)}"
        logger.info(f"Generated authorization URL with scopes: {scopes}")
        return url

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for user access token.

        Args:
            authorization_code: Authorization code from OAuth callback

        Returns:
            Token information including access_token, expires_in, etc.
        """
        try:
            url = f"{self.graph_base_url}/{self.graph_api_version}/oauth/access_token"
            params = {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": self.redirect_uri,
                "code": authorization_code,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise MetaOAuthError("No access token received from code exchange")

            # Store token with metadata
            user_id = token_data.get("user_id", "unknown")
            self._user_tokens[user_id] = {
                "access_token": access_token,
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in"),
                "created_at": datetime.now(),
                "user_id": user_id,
            }

            logger.info(f"Successfully exchanged code for token for user: {user_id}")
            return token_data

        except requests.RequestException as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise MetaOAuthError(f"Code exchange failed: {e}")

    def get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """
        Exchange short-lived token for long-lived token (60 days).

        Args:
            short_lived_token: Short-lived access token

        Returns:
            Long-lived token information
        """
        try:
            url = f"{self.graph_base_url}/{self.graph_api_version}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": short_lived_token,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            logger.info("Successfully obtained long-lived token")
            return token_data

        except requests.RequestException as e:
            logger.error(f"Failed to get long-lived token: {e}")
            raise MetaOAuthError(f"Long-lived token exchange failed: {e}")

    def refresh_instagram_token(self, user_id: str) -> Dict[str, Any]:
        """
        Refresh Instagram Basic Display API token.

        Args:
            user_id: User identifier for token refresh

        Returns:
            New token information
        """
        try:
            if user_id not in self._user_tokens:
                raise MetaOAuthError("No token found for user")

            old_token = self._user_tokens[user_id]["access_token"]

            url = f"{self.instagram_base_url}/refresh_access_token"
            params = {"grant_type": "ig_refresh_token", "access_token": old_token}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            new_token = token_data.get("access_token")

            if not new_token:
                raise MetaOAuthError("No new token received from refresh")

            # Update stored token
            self._user_tokens[user_id].update(
                {
                    "access_token": new_token,
                    "expires_in": token_data.get(
                        "expires_in", 60 * 24 * 60
                    ),  # 60 days default
                    "refreshed_at": datetime.now(),
                }
            )

            logger.info(f"Successfully refreshed Instagram token for user: {user_id}")
            return token_data

        except requests.RequestException as e:
            logger.error(f"Failed to refresh Instagram token: {e}")
            raise MetaOAuthError(f"Token refresh failed: {e}")

    def get_user_token(self, user_id: str) -> Optional[str]:
        """
        Get stored user access token.

        Args:
            user_id: User identifier

        Returns:
            User access token or None if not found
        """
        user_data = self._user_tokens.get(user_id)
        if user_data:
            return user_data.get("access_token")
        return None

    def validate_token(self, token: str) -> bool:
        """
        Validate if a token is still valid.

        Args:
            token: Access token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            url = f"{self.graph_base_url}/debug_token"
            params = {"input_token": token, "access_token": self.get_app_token()}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            token_data = data.get("data", {})

            is_valid = token_data.get("is_valid", False)
            if is_valid:
                logger.debug("Token validation successful")
            else:
                logger.warning(
                    f"Token validation failed: {token_data.get('error', 'Unknown error')}"
                )

            return is_valid

        except (requests.RequestException, KeyError) as e:
            logger.error(f"Token validation error: {e}")
            return False

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current OAuth connection status and health.

        Returns:
            Dictionary with connection status information
        """
        status = {
            "app_id": self.app_id,
            "has_app_token": bool(self._app_token),
            "app_token_valid": False,
            "user_tokens_count": len(self._user_tokens),
            "production_mode": os.getenv("PRODUCTION_MODE", "false").lower() == "true",
        }

        # Validate app token if we have one
        if self._app_token:
            try:
                status["app_token_valid"] = self.validate_token(self._app_token)
            except Exception as e:
                status["app_token_valid"] = False
                status["app_token_error"] = str(e)

        return status
