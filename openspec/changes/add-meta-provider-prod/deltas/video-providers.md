# Delta: Video Providers Specification

## Current State
Meta provider exists only as stub implementation with mock data. No real API integration with Meta platforms.

## Target State
Full Meta provider implementation with OAuth2 authentication and real API integration for Facebook and Instagram.

## Changes Required

### 1. Meta Provider Class Enhancement

**Current (`core/providers/meta.py`)**:
```python
class MetaProvider(BaseVideoProvider):
    def __init__(self):
        super().__init__()
        # Mock implementation only
```

**Target**:
```python
class MetaProvider(BaseVideoProvider):
    def __init__(self, oauth_client: MetaOAuth2Client = None):
        super().__init__()
        self.oauth_client = oauth_client or MetaOAuth2Client()
        self.base_url = "https://graph.facebook.com/v18.0"
        self.production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
```

### 2. New OAuth2 Client Integration

**Add**:
```python
class MetaOAuth2Client:
    """Handles OAuth2 authentication for Meta APIs"""

    def __init__(self):
        self.client_id = os.getenv('META_APP_ID')
        self.client_secret = os.getenv('META_APP_SECRET')
        self.redirect_uri = os.getenv('META_REDIRECT_URI')

    async def get_app_token(self) -> str:
        """Generate app-level token for server-to-server requests"""

    async def get_user_token(self, authorization_code: str) -> str:
        """Exchange auth code for user access token"""

    async def refresh_token(self, refresh_token: str) -> str:
        """Refresh expired access token"""
```

### 3. Real API Methods Implementation

**Replace mock methods with**:
```python
async def search_instagram_hashtag(self, hashtag: str, max_results: int = 20) -> List[VideoResult]:
    """Real Instagram hashtag search via Graph API"""

async def search_facebook_page(self, page_id: str, max_results: int = 20) -> List[VideoResult]:
    """Real Facebook page content search via Graph API"""

async def get_media_details(self, media_id: str, platform: str) -> VideoResult:
    """Get detailed media information from Meta APIs"""
```

### 4. Enhanced Error Handling

**Add Meta-specific error classes**:
```python
class MetaAPIError(Exception):
    """Base exception for Meta API errors"""

class MetaRateLimitError(MetaAPIError):
    """Raised when API rate limit exceeded"""

class MetaAuthError(MetaAPIError):
    """Raised when authentication fails"""
```

### 5. Fallback Implementation

**Add**:
```python
async def search_with_fallback(self, params: SearchParams) -> List[VideoResult]:
    """
    Search with automatic fallback to mock when production APIs fail
    """
    try:
        if self.production_mode:
            return await self.search_production(params)
        else:
            return await self.search_mock(params)
    except (MetaAPIError, OAuthError) as e:
        logger.warning(f"Meta API failed: {e}, falling back to mock")
        return await self.search_mock(params)
```

### 6. Configuration Updates

**Add environment variables**:
```bash
# .env.example additions
META_APP_ID=your_facebook_app_id
META_APP_SECRET=your_facebook_app_secret
META_REDIRECT_URI=http://localhost:8501/oauth/callback
PRODUCTION_MODE=false
META_API_VERSION=v18.0
```

## Updated Interface Specification

### MetaProvider Interface
```python
class MetaProvider(BaseVideoProvider):
    """Meta (Facebook + Instagram) video provider with real API integration"""

    def __init__(self, oauth_client: MetaOAuth2Client = None):
        """Initialize with optional OAuth2 client"""

    async def authenticate(self) -> bool:
        """Establish OAuth2 connection with Meta APIs"""

    async def search(self, params: SearchParams) -> List[VideoResult]:
        """Search Meta content with automatic fallback"""

    async def get_capabilities(self) -> ProviderCapabilities:
        """Return enhanced capabilities for production mode"""

    async def health_check(self) -> Dict[str, Any]:
        """Check API connectivity and authentication status"""
```

### New Dependencies
```python
# requirements.txt additions
requests-oauthlib>=1.3.1
facebook-sdk>=3.1.0
httpx>=0.24.0  # For async HTTP requests
```

## Migration Path

### Phase 1: Foundation
1. Add OAuth2 client without breaking existing mock functionality
2. Add environment configuration
3. Create new provider methods alongside existing ones

### Phase 2: Integration
1. Update search methods to use real APIs when PRODUCTION_MODE=true
2. Implement fallback mechanism
3. Add error handling specific to Meta APIs

### Phase 3: Cleanup
1. Remove deprecated mock-only methods
2. Update provider capabilities to reflect real functionality
3. Add comprehensive testing

## Testing Strategy

### Unit Tests
- OAuth2 client initialization and token management
- API request/response mapping
- Error handling for various Meta API failures

### Integration Tests
- End-to-end search with Meta sandbox APIs
- Fallback behavior when production APIs unavailable
- Authentication flow testing

### Mock Tests
- Ensure fallback maintains existing functionality
- Verify data mapping consistency
- Test rate limiting behavior

## Security Considerations

1. **Token Storage**: Never commit tokens to repository
2. **Rate Limits**: Implement proper backoff and monitoring
3. **Permission Scopes**: Use minimum required API permissions
4. **Token Rotation**: Implement automatic token refresh
5. **API Versioning**: Pin to specific Graph API version

## Performance Implications

- **Additional Dependencies**: OAuth2 and HTTP client libraries
- **Network Latency**: Real API calls vs instant mock responses
- **Rate Limiting**: Need to respect Meta API quotas
- **Caching**: Opportunity to cache frequent requests
- **Connection Pooling**: Reuse HTTP connections for efficiency