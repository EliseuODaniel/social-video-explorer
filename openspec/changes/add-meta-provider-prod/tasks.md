## 1. Meta Provider OAuth2 Implementation
- [ ] 1.1 Create OAuth2 client class for Facebook Graph API
- [ ] 1.2 Create OAuth2 client class for Instagram Basic Display API
- [ ] 1.3 Implement unified token management (single app token for FB+IG)
- [ ] 1.4 Add token refresh and error handling logic
- [ ] 1.5 Create secure credential storage in environment variables

## 2. Meta API Integration
- [ ] 2.1 Replace existing Meta provider stub with real API implementation
- [ ] 2.2 Implement Facebook Graph API video/photo search endpoints
- [ ] 2.3 Implement Instagram hashtag media search endpoints
- [ ] 2.4 Add API-specific error handling and response validation
- [ ] 2.5 Add fallback mechanism to mock provider on API failures

## 3. Meta to VideoResult Mapping
- [ ] 3.1 Map Facebook media fields to VideoResult schema
- [ ] 3.2 Map Instagram media fields to VideoResult schema
- [ ] 3.3 Handle platform-specific fields in raw_payload
- [ ] 3.4 Add metadata processing (created_at, media_type, dimensions)
- [ ] 3.5 Add URL normalization and thumbnail extraction

## 4. Search Service Enhancement
- [ ] 4.1 Update search_service.py to integrate real Meta provider
- [ ] 4.2 Add production mode detection and provider selection
- [ ] 4.3 Add error handling for OAuth failures and API limits
- [ ] 4.4 Add fallback to mock when production unavailable
- [ ] 4.5 Add search parameter validation for Meta APIs

## 5. UI Production Status Updates
- [ ] 5.1 Add production mode indicator in Streamlit UI
- [ ] 5.2 Add OAuth connection status display
- [ ] 5.3 Add API health check indicators
- [ ] 5.4 Add error messages for authentication issues
- [ ] 5.5 Add toggle for production vs mock mode (testing)

## 6. Configuration and Environment Setup
- [ ] 6.1 Add Meta app credentials to .env.example
- [ ] 6.2 Add OAuth redirect URI configuration
- [ ] 6.3 Add production mode environment variable
- [ ] 6.4 Add API endpoint configuration
- [ ] 6.5 Add rate limiting configuration placeholders

## 7. Testing Implementation
- [ ] 7.1 Create unit tests for OAuth2 client implementations
- [ ] 7.2 Create integration tests with Meta API sandbox
- [ ] 7.3 Create mock tests for fallback scenarios
- [ ] 7.4 Add tests for VideoResult mapping accuracy
- [ ] 7.5 Add end-to-end tests for production search workflow

## 8. Documentation and Deployment
- [ ] 8.1 Update README.md with Meta provider setup instructions
- [ ] 8.2 Add OAuth2 setup guide for Meta Developers Console
- [ ] 8.3 Document API limitations and rate limits
- [ ] 8.4 Add troubleshooting guide for common authentication issues
- [ ] 8.5 Update requirements.txt with new dependencies