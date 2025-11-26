# Tasks: Add Meta Provider Rate Limiting

## 1. Rate Limiting Implementation
- [ ] 1.1 Create RateLimiter class with token bucket algorithm
- [ ] 1.2 Configure limits: 150 requests/hour per app
- [ ] 1.3 Implement per-endpoint limits (search, hashtag, user content)
- [ ] 1.4 Add rate limit headers handling from Meta API
- [ ] 1.5 Configure circuit breaker thresholds

## 2. Memory Cache System
- [ ] 2.1 Implement LRUCache utility class with TTL support
- [ ] 2.2 Create token cache (TTL: 1 hour) for OAuth tokens
- [ ] 2.3 Create search results cache (TTL: 15 minutes)
- [ ] 2.4 Create health status cache (TTL: 5 minutes)
- [ ] 2.5 Create hashtag cache (TTL: 1 hour) for popular queries
- [ ] 2.6 Implement cache warming for common searches

## 3. Metrics and Logging
- [ ] 3.1 Add structured logging for rate limit events
- [ ] 3.2 Implement request counters per endpoint
- [ ] 3.3 Create cache hit ratio tracking
- [ ] 3.4 Add latency metrics for API calls vs cache
- [ ] 3.5 Create error rate monitoring
- [ ] 3.6 Implement Prometheus-compatible metrics format

## 4. Meta Provider Integration
- [ ] 4.1 Integrate RateLimiter into MetaProvider class
- [ ] 4.2 Add cache layer before API calls
- [ ] 4.3 Implement retry logic with exponential backoff
- [ ] 4.4 Add circuit breaker for API failures
- [ ] 4.5 Update health check to include rate limiter status
- [ ] 4.6 Handle 429 Too Many Requests errors gracefully

## 5. Search Service Updates
- [ ] 5.1 Update SearchService to respect rate limits
- [ ] 5.2 Add cache-first search strategy
- [ ] 5.3 Implement concurrent request coordination
- [ ] 5.4 Add rate limit awareness to search selection
- [ ] 5.5 Update system health to include cache metrics

## 6. UI Enhancements
- [ ] 6.1 Add rate limiting status indicator in sidebar
- [ ] 6.2 Create "requests remaining" counter display
- [ ] 6.3 Show cache status (hit/miss indicators)
- [ ] 6.4 Add rate limit warning messages
- [ ] 6.5 Implement graceful error messages for 429 errors
- [ ] 6.6 Add "cache info" section in about dialog

## 7. Configuration Management
- [ ] 7.1 Add rate limiting config to .env.example
- [ ] 7.2 Add cache configuration options
- [ ] 7.3 Create config validation utilities
- [ ] 7.4 Support different rate limits per environment
- [ ] 7.5 Add circuit breaker configuration

## 8. Testing Implementation
- [ ] 8.1 Create unit tests for RateLimiter class
- [ ] 8.2 Write cache utility tests with TTL scenarios
- [ ] 8.3 Test rate limiting behavior with mock APIs
- [ ] 8.4 Test circuit breaker triggering and recovery
- [ ] 8.5 Create integration tests with real cache
- [ ] 8.6 Test UI status indicators and error handling
- [ ] 8.7 Performance tests for cache hit ratios
- [ ] 8.8 Load tests for rate limit enforcement

## 9. Documentation and Deployment
- [ ] 9.1 Update README.md with rate limiting info
- [ ] 9.2 Document cache configuration options
- [ ] 9.3 Create rate limiting troubleshooting guide
- [ ] 9.4 Add metrics interpretation guide
- [ ] 9.5 Update deployment checklist

## Success Metrics
- [ ] **Rate Limiting**: <1% of requests hit API limits
- [ ] **Cache Hit Ratio**: >50% for repeated queries
- [ ] **Error Rate**: <0.5% rate limit related errors
- [ ] **Performance**: <200ms response time for cached results
- [ ] **UI Responsiveness**: Real-time status indicators working

## Testing Strategy
- Unit tests: Individual component isolation
- Integration tests: End-to-end flow validation
- Performance tests: Load and stress testing
- Chaos tests: Failure scenario validation
- Monitoring tests: Metrics and logging verification