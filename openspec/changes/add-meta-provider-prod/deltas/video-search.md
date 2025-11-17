# Delta: Video Search Service Specification

## Current State
SearchService operates with mock providers only, basic single-provider search, minimal error handling, and no production mode awareness.

## Target State
Enhanced search service supporting real Meta provider integration, automatic fallback mechanisms, production mode detection, and comprehensive error handling.

## Changes Required

### 1. Production Mode Detection

**Current initialization**:
```python
class SearchService:
    def __init__(self):
        self.providers = {
            'mock': MockProvider(),
            'meta': MetaProvider()  # mock only
        }
```

**Target initialization**:
```python
class SearchService:
    def __init__(self):
        self.production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
        self.providers = self._initialize_providers()

    def _initialize_providers(self) -> Dict[str, BaseVideoProvider]:
        providers = {}

        # Always include mock for fallback
        providers['mock'] = MockProvider()

        # Initialize Meta provider based on mode
        if self.production_mode:
            try:
                oauth_client = MetaOAuth2Client()
                providers['meta'] = MetaProvider(oauth_client)
                providers['instagram'] = providers['meta']  # Alias
                providers['facebook'] = providers['meta']   # Alias
            except Exception as e:
                logger.warning(f"Failed to initialize Meta provider: {e}, using mock")
                providers['meta'] = MockProvider()
        else:
            providers['meta'] = MockProvider()
            providers['instagram'] = MockProvider()
            providers['facebook'] = MockProvider()

        return providers
```

### 2. Enhanced Search Method with Fallback

**Current search method**:
```python
async def search(self, params: SearchParams) -> List[VideoResult]:
    provider = self.providers.get(params.platform)
    if not provider:
        raise ValueError(f"Provider {params.platform} not supported")
    return await provider.search(params)
```

**Target search method**:
```python
async def search(self, params: SearchParams) -> List[VideoResult]:
    """
    Enhanced search with automatic fallback and error handling
    """
    # Normalize platform aliases
    platform = self._normalize_platform(params.platform)

    # Get primary provider
    primary_provider = self.providers.get(platform)
    if not primary_provider:
        raise ValueError(f"Provider {platform} not supported")

    try:
        # Attempt search with primary provider
        results = await primary_provider.search(params)
        await self._log_search_success(platform, len(results))
        return results

    except (MetaAPIError, OAuthError, NetworkError) as e:
        # Handle production API failures with fallback
        logger.warning(f"Primary provider {platform} failed: {e}, attempting fallback")
        return await self._search_with_fallback(platform, params, e)

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in search: {e}")
        raise SearchServiceError(f"Search failed: {e}")

async def _search_with_fallback(self, platform: str, params: SearchParams, original_error: Exception) -> List[VideoResult]:
    """Fallback to mock provider when production fails"""

    # Use mock provider for fallback
    mock_provider = self.providers.get('mock')
    if not mock_provider:
        raise original_error  # Re-raise if no fallback available

    try:
        fallback_results = await mock_provider.search(params)
        await self._log_fallback_success(platform, len(fallback_results), str(original_error))
        return fallback_results

    except Exception as fallback_error:
        logger.error(f"Fallback provider also failed: {fallback_error}")
        raise original_error  # Re-raise original error
```

### 3. Multi-Provider Search Support

**Add multi-provider capability**:
```python
async def search_multiple(self, params: SearchParams, platforms: List[str]) -> Dict[str, List[VideoResult]]:
    """
    Search across multiple platforms concurrently
    """
    normalized_platforms = [self._normalize_platform(p) for p in platforms]

    # Create concurrent search tasks
    search_tasks = []
    for platform in normalized_platforms:
        if platform in self.providers:
            task = self._search_single_platform(platform, params)
            search_tasks.append((platform, task))

    # Execute searches concurrently with error handling
    results = {}
    for platform, task in search_tasks:
        try:
            platform_results = await task
            results[platform] = platform_results
        except Exception as e:
            logger.warning(f"Platform {platform} failed in multi-search: {e}")
            results[platform] = []  # Return empty list for failed platform

    return results

async def _search_single_platform(self, platform: str, params: SearchParams) -> List[VideoResult]:
    """Single platform search with fallback logic"""
    return await self.search(SearchParams(
        query=params.query,
        platform=platform,
        max_results=params.max_results
    ))
```

### 4. Provider Health Monitoring

**Add health checking**:
```python
async def check_provider_health(self) -> Dict[str, Dict[str, Any]]:
    """
    Check health status of all providers
    """
    health_status = {}

    for platform, provider in self.providers.items():
        try:
            if hasattr(provider, 'health_check'):
                status = await provider.health_check()
            else:
                # Basic health check for providers without specific method
                status = {
                    'status': 'unknown',
                    'response_time': None,
                    'last_check': datetime.utcnow().isoformat()
                }

            health_status[platform] = status

        except Exception as e:
            health_status[platform] = {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }

    return health_status

def get_service_status(self) -> Dict[str, Any]:
    """
    Get overall search service status
    """
    return {
        'production_mode': self.production_mode,
        'available_providers': list(self.providers.keys()),
        'platform_aliases': {
            'meta': ['meta', 'facebook', 'instagram'],
        },
        'supported_operations': ['single_search', 'multi_search', 'health_check']
    }
```

### 5. Enhanced Search Parameters

**Extend SearchParams for Meta integration**:
```python
# core/schemas.py extension
class SearchParams(BaseModel):
    # Existing fields...
    query: str
    platform: str
    max_results: int = 20

    # New fields for Meta integration
    include_fallback: bool = True
    timeout_seconds: int = 30
    retry_attempts: int = 1
    # Meta-specific fields
    hashtag_filter: Optional[str] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    media_type_filter: Optional[str] = None  # 'video', 'photo', 'all'
```

### 6. Search Service Error Classes

**Add specific error handling**:
```python
class SearchServiceError(Exception):
    """Base error for search service operations"""

class ProviderNotAvailableError(SearchServiceError):
    """Raised when requested provider is not available"""

class AllProvidersFailedError(SearchServiceError):
    """Raised when all providers (including fallback) fail"""

class SearchTimeoutError(SearchServiceError):
    """Raised when search operation times out"""

class InvalidSearchParametersError(SearchServiceError):
    """Raised when search parameters are invalid"""
```

## Updated Interface Specification

### SearchService Class
```python
class SearchService:
    """Enhanced search service with production Meta integration and fallback"""

    def __init__(self):
        """Initialize service with production mode detection and provider setup"""

    async def search(self, params: SearchParams) -> List[VideoResult]:
        """Single provider search with automatic fallback"""

    async def search_multiple(self, params: SearchParams, platforms: List[str]) -> Dict[str, List[VideoResult]]:
        """Multi-provider concurrent search"""

    async def check_provider_health(self) -> Dict[str, Dict[str, Any]]:
        """Health status monitoring for all providers"""

    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service configuration and status"""

    def _normalize_platform(self, platform: str) -> str:
        """Normalize platform names and aliases"""

    async def _search_with_fallback(self, platform: str, params: SearchParams, error: Exception) -> List[VideoResult]:
        """Fallback mechanism for failed production providers"""
```

## Configuration Updates

### Environment Variables
```bash
# .env.example additions
PRODUCTION_MODE=false                    # Enable/disable real Meta APIs
SEARCH_TIMEOUT_SECONDS=30              # Default search timeout
SEARCH_RETRY_ATTEMPTS=1                # Default retry count
ENABLE_CONCURRENT_SEARCH=true          # Allow multi-provider searches
LOG_SEARCH_METRICS=true                # Enable search performance logging
```

### Service Configuration
```python
# config/search_config.py
SEARCH_CONFIG = {
    'default_timeout': int(os.getenv('SEARCH_TIMEOUT_SECONDS', 30)),
    'default_retry_attempts': int(os.getenv('SEARCH_RETRY_ATTEMPTS', 1)),
    'enable_concurrent': os.getenv('ENABLE_CONCURRENT_SEARCH', 'true').lower() == 'true',
    'log_metrics': os.getenv('LOG_SEARCH_METRICS', 'true').lower() == 'true',
    'platform_aliases': {
        'meta': ['meta', 'facebook', 'instagram'],
    },
    'rate_limits': {
        'meta': {'requests_per_minute': 200, 'burst_limit': 50},
        'mock': {'unlimited': True}
    }
}
```

## Testing Strategy

### Unit Tests
- Provider initialization logic for production vs mock modes
- Search method error handling and fallback mechanisms
- Platform normalization and alias handling
- Health check functionality

### Integration Tests
- End-to-end search with real Meta APIs (sandbox)
- Multi-provider concurrent search execution
- Fallback behavior when production APIs fail
- Timeout and retry logic testing

### Performance Tests
- Concurrent search performance with multiple providers
- Memory usage during large result sets
- Response time comparison between production and mock modes

## Migration Path

### Phase 1: Non-Breaking Enhancements
1. Add new methods without changing existing ones
2. Implement provider initialization logic
3. Add configuration support

### Phase 2: Enhanced Search Logic
1. Update search method with fallback
2. Add multi-provider search support
3. Implement health checking

### Phase 3: Cleanup and Optimization
1. Remove deprecated methods
2. Optimize concurrent search performance
3. Add comprehensive metrics and logging

## Performance Considerations

- **Concurrent Searches**: Use asyncio.gather() for parallel provider execution
- **Connection Reuse**: Implement connection pooling for Meta API requests
- **Response Caching**: Cache frequent search results to reduce API calls
- **Rate Limiting**: Respect Meta API quotas with intelligent throttling
- **Memory Management**: Stream large result sets to avoid memory overflow

## Monitoring and Observability

### Metrics to Track
- Search request volume by platform
- Success/failure rates per provider
- Fallback usage frequency
- Average response times
- API rate limit hits

### Logging Strategy
- Structured JSON logging for search operations
- Error categorization and alerting
- Performance metrics aggregation
- Provider health status changes