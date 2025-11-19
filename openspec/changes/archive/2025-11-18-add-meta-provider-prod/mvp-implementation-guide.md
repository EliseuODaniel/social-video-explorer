# MVP Implementation Guide: Add Meta Provider Production Support

## Step-by-Step Implementation

### Phase 1: OAuth2 Foundation (Day 1-2)

#### 1.1 Setup OAuth2 Dependencies
```bash
# Add to requirements.txt
requests-oauthlib>=1.3.1
facebook-sdk>=3.1.0
python-dotenv>=0.19.0
```

#### 1.2 Create OAuth2 Client (`core/providers/oauth_client.py`)
```python
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

class MetaOAuth2Client:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv('META_APP_ID')
        self.client_secret = os.getenv('META_APP_SECRET')
        self.redirect_uri = os.getenv('META_REDIRECT_URI')

    def get_app_token(self):
        # Implement Facebook App Token generation
        # Used for server-to-server requests
        pass

    def get_user_token(self, authorization_code):
        # Exchange authorization code for user access token
        pass
```

#### 1.3 Environment Setup
```bash
# Add to .env.example
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_REDIRECT_URI=http://localhost:8501/oauth/callback
PRODUCTION_MODE=false
```

### Phase 2: Meta Provider Implementation (Day 3-4)

#### 2.1 Update Meta Provider (`core/providers/meta.py`)
```python
from .oauth_client import MetaOAuth2Client
from .base import BaseVideoProvider
from ..schemas import VideoResult, SearchParams

class MetaProvider(BaseVideoProvider):
    def __init__(self, oauth_client: MetaOAuth2Client):
        super().__init__()
        self.oauth_client = oauth_client
        self.base_url = "https://graph.facebook.com/v18.0"

    async def search_hashtag(self, hashtag: str, max_results: int = 20) -> List[VideoResult]:
        # Real Instagram hashtag search implementation
        # Map Instagram media to VideoResult
        pass

    async def search_page_content(self, page_id: str, max_results: int = 20) -> List[VideoResult]:
        # Real Facebook page content search
        # Map Facebook posts/videos to VideoResult
        pass
```

#### 2.2 Fallback Implementation
```python
async def search_with_fallback(self, params: SearchParams) -> List[VideoResult]:
    try:
        return await self.search_production(params)
    except (OAuthError, APIError, RateLimitError) as e:
        logger.warning(f"Meta API failed: {e}, falling back to mock")
        return await self.search_mock(params)
```

### Phase 3: Data Mapping (Day 5)

#### 3.1 Instagram Media Mapping
```python
def map_instagram_media_to_video_result(media_item: dict) -> VideoResult:
    return VideoResult(
        id=f"ig_{media_item['id']}",
        title=media_item.get('caption', 'Instagram Post')[:100],
        url=media_item['permalink'],
        thumbnail_url=media_item.get('media_url'),
        created_at=datetime.fromisoformat(media_item['timestamp']),
        platform='instagram',
        media_type=media_item['media_type'],
        raw_payload=media_item
    )
```

#### 3.2 Facebook Content Mapping
```python
def map_facebook_post_to_video_result(post_item: dict) -> VideoResult:
    return VideoResult(
        id=f"fb_{post_item['id']}",
        title=post_item.get('message', 'Facebook Post')[:100],
        url=f"https://facebook.com/{post_item['id']}",
        thumbnail_url=post_item.get('full_picture'),
        created_at=datetime.fromisoformat(post_item['created_time']),
        platform='facebook',
        media_type='video' if 'video' in post_item else 'photo',
        raw_payload=post_item
    )
```

### Phase 4: Search Service Integration (Day 6)

#### 4.1 Update Search Service
```python
# core/services/search_service.py
class SearchService:
    def __init__(self):
        production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
        if production_mode:
            self.meta_provider = MetaProvider(MetaOAuth2Client())
        else:
            self.meta_provider = MockMetaProvider()

    async def search(self, params: SearchParams) -> List[VideoResult]:
        if params.platform in ['instagram', 'facebook', 'meta']:
            return await self.meta_provider.search(params)
        # Handle other providers...
```

### Phase 5: UI Production Status (Day 7)

#### 5.1 Add Status Indicators
```python
# ui/streamlit_app.py
def show_production_status():
    production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

    if production_mode:
        st.success("🟢 Production Mode - Meta APIs Active")
        # Show OAuth status
        if check_oauth_valid():
            st.info("✅ Meta Authentication Valid")
        else:
            st.error("❌ Meta Authentication Required")
    else:
        st.warning("🟡 Mock Mode - Using Sample Data")
```

### Phase 6: Testing Implementation (Day 8)

#### 6.1 Unit Tests
```python
# tests/test_meta_provider.py
class TestMetaProvider:
    def test_instagram_mapping(self):
        # Test Instagram media -> VideoResult mapping
        pass

    def test_oauth_client_creation(self):
        # Test OAuth client initialization
        pass

    def test_fallback_mechanism(self):
        # Test fallback to mock on API failure
        pass
```

#### 6.2 Integration Tests
```python
# tests/test_search_integration.py
class TestSearchIntegration:
    @pytest.mark.asyncio
    async def test_production_search(self):
        # Integration test with real Meta APIs (use sandbox)
        pass
```

## Implementation Checklist

### OAuth2 Setup
- [ ] Meta App configured in Facebook Developers Console
- [ ] OAuth2 redirect URI registered
- [ ] App ID and Secret available
- [ ] Test user accounts configured

### API Integration
- [ ] Facebook Graph API endpoints working
- [ ] Instagram Basic Display API working
- [ ] Token refresh mechanism implemented
- [ ] Rate limiting handling added

### Data Mapping
- [ ] Instagram media fields mapped correctly
- [ ] Facebook content fields mapped correctly
- [ ] raw_payload preservation verified
- [ ] Date/time handling consistent

### Testing Coverage
- [ ] Unit tests for OAuth2 client
- [ ] Unit tests for data mapping
- [ ] Integration tests with sandbox
- [ ] Fallback mechanism tests
- [ ] UI status indicator tests

## Validation Steps

### 1. Basic Functionality
```bash
# Test OAuth flow
python -m core.providers.oauth_client

# Test Meta provider
python -m core.providers.meta --test-mode=sandbox

# Test search integration
python -m core.services.search_service --query=test --platform=instagram
```

### 2. Production Validation
```bash
# Set production mode
export PRODUCTION_MODE=true

# Run Streamlit with real APIs
streamlit run ui/streamlit_app.py

# Test search with real Meta data
```

### 3. Fallback Testing
```bash
# Test with invalid credentials
export META_APP_ID=invalid

# Verify fallback to mock mode works
python -m core.services.search_service --query=test
```

## Troubleshooting

### Common Issues
1. **OAuth Token Issues**: Check app permissions and redirect URIs
2. **API Rate Limits**: Implement exponential backoff
3. **Field Mapping**: Verify API response structure matches expected format
4. **Fallback Logic**: Ensure mock provider handles all error scenarios

### Debug Commands
```bash
# Check OAuth status
python -c "from core.providers.oauth_client import MetaOAuth2Client; print(MetaOAuth2Client().get_app_token())"

# Test API endpoints directly
curl -H "Authorization: Bearer $TOKEN" "https://graph.facebook.com/v18.0/me/accounts"
```

## Production Deployment

### Environment Variables Required
- `META_APP_ID`: Facebook App ID
- `META_APP_SECRET`: Facebook App Secret
- `META_REDIRECT_URI`: OAuth callback URL
- `PRODUCTION_MODE`: Set to 'true' for production APIs

### Security Considerations
- Never commit credentials to repository
- Use environment variables for secrets
- Implement token rotation policy
- Monitor API usage and rate limits
- Add logging for audit trails

### Performance Optimization
- Cache OAuth tokens with appropriate TTL
- Implement request deduplication
- Add connection pooling for API requests
- Monitor response times and adjust timeouts