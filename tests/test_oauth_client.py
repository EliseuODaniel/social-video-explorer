"""
Tests for Meta OAuth2 client implementation
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException

from core.providers.oauth_client import MetaOAuth2Client, MetaOAuthError


class TestMetaOAuth2Client:
    """Test cases for MetaOAuth2Client."""

    def setup_method(self):
        """Set up test environment."""
        # Set test environment variables
        os.environ["META_APP_ID"] = "test_app_id"
        os.environ["META_APP_SECRET"] = "test_app_secret"
        os.environ["META_REDIRECT_URI"] = "http://localhost:8501/oauth/callback"

    def teardown_method(self):
        """Clean up after tests."""
        # Remove test environment variables
        for key in ["META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"]:
            if key in os.environ:
                del os.environ[key]

    def test_initialization_with_valid_credentials(self):
        """Test successful initialization with valid credentials."""
        client = MetaOAuth2Client()
        assert client.app_id == "test_app_id"
        assert client.app_secret == "test_app_secret"
        assert client.redirect_uri == "http://localhost:8501/oauth/callback"

    def test_initialization_without_credentials_raises_error(self):
        """Test initialization fails without required credentials."""
        os.environ.pop("META_APP_ID")

        with pytest.raises(
            MetaOAuthError, match="META_APP_ID and META_APP_SECRET.*required"
        ):
            MetaOAuth2Client()

    @patch("requests.get")
    def test_get_app_token_success(self, mock_get):
        """Test successful app token retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "test_token"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = MetaOAuth2Client()
        token = client.get_app_token()

        assert token == "test_token"
        assert client._app_token == "test_token"
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_app_token_request_failure(self, mock_get):
        """Test app token retrieval handles request failures."""
        mock_get.side_effect = RequestException("Network error")

        client = MetaOAuth2Client()
        with pytest.raises(MetaOAuthError, match="Failed to obtain app token"):
            client.get_app_token()

    @patch("requests.get")
    def test_get_app_token_no_token_in_response(self, mock_get):
        """Test app token retrieval handles missing token in response."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = MetaOAuth2Client()
        with pytest.raises(MetaOAuthError, match="No access token received"):
            client.get_app_token()

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        client = MetaOAuth2Client()
        url = client.get_authorization_url()

        assert "facebook.com" in url
        assert "test_app_id" in url
        assert "http%3A%2F%2Flocalhost%3A8501%2Foauth%2Fcallback" in url  # URL encoded
        assert "client_credentials" not in url  # Should use authorization code flow

    @patch("requests.get")
    def test_exchange_code_for_token_success(self, mock_get):
        """Test successful code exchange for access token."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "user_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "user_id": "test_user",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = MetaOAuth2Client()
        token_data = client.exchange_code_for_token("test_code")

        assert token_data["access_token"] == "user_token"
        assert client.get_user_token("test_user") == "user_token"

    @patch("requests.get")
    def test_get_long_lived_token_success(self, mock_get):
        """Test successful exchange to long-lived token."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "long_lived_token",
            "expires_in": 5184000,  # 60 days
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = MetaOAuth2Client()
        token_data = client.get_long_lived_token("short_lived_token")

        assert token_data["access_token"] == "long_lived_token"
        assert token_data["expires_in"] == 5184000

    @patch("requests.get")
    def test_refresh_instagram_token_success(self, mock_get):
        """Test successful Instagram token refresh."""
        # Setup user token first
        client = MetaOAuth2Client()
        client._user_tokens["test_user"] = {
            "access_token": "old_instagram_token",
            "created_at": client._user_tokens.get("test_user", {}).get("created_at"),
        }

        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_instagram_token",
            "expires_in": 5184000,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        token_data = client.refresh_instagram_token("test_user")

        assert token_data["access_token"] == "new_instagram_token"
        assert client.get_user_token("test_user") == "new_instagram_token"

    def test_refresh_instagram_token_no_stored_token(self):
        """Test Instagram token refresh fails without stored token."""
        client = MetaOAuth2Client()

        with pytest.raises(MetaOAuthError, match="No token found for user"):
            client.refresh_instagram_token("nonexistent_user")

    @patch("requests.get")
    def test_validate_token_success(self, mock_get):
        """Test successful token validation."""
        client = MetaOAuth2Client()
        client._app_token = "test_app_token"

        # Mock get_app_token to return the existing token
        def mock_get_app_token():
            return "test_app_token"

        client.get_app_token = mock_get_app_token

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"is_valid": True, "app_id": "test_app_id"}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        is_valid = client.validate_token("test_token")
        assert is_valid is True

    @patch("requests.get")
    def test_validate_token_invalid(self, mock_get):
        """Test token validation with invalid token."""
        client = MetaOAuth2Client()

        # Mock get_app_token to return existing token
        def mock_get_app_token():
            return "test_app_token"
        client.get_app_token = mock_get_app_token

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"is_valid": False, "error": "Invalid OAuth access token"}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        is_valid = client.validate_token("invalid_token")
        assert is_valid is False

    def test_get_user_token_not_found(self):
        """Test getting non-existent user token."""
        client = MetaOAuth2Client()
        token = client.get_user_token("nonexistent_user")
        assert token is None

    def test_get_connection_status(self):
        """Test connection status retrieval."""
        client = MetaOAuth2Client()
        client._app_token = "test_token"

        status = client.get_connection_status()

        assert status["app_id"] == "test_app_id"
        assert status["has_app_token"] is True
        assert status["user_tokens_count"] == 0
        assert "production_mode" in status

    def test_get_connection_status_no_token(self):
        """Test connection status without app token."""
        client = MetaOAuth2Client()

        status = client.get_connection_status()

        assert status["app_id"] == "test_app_id"
        assert status["has_app_token"] is False
        assert status["app_token_valid"] is False

    @patch("requests.get")
    def test_validate_token_request_exception(self, mock_get):
        """Test token validation handles request exceptions."""
        client = MetaOAuth2Client()

        # Mock get_app_token to return existing token
        def mock_get_app_token():
            return "test_app_token"
        client.get_app_token = mock_get_app_token

        # Mock the validate_token's get request to fail
        def mock_validate_get(*args, **kwargs):
            raise RequestException("Network error")

        mock_get.side_effect = mock_validate_get

        is_valid = client.validate_token("test_token")
        assert is_valid is False
