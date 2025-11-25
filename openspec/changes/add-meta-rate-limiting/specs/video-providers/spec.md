## ADDED Requirements

### Requirement: Provider Rate Limiting and Resilience
The system SHALL implement rate limiting and resilience patterns for Meta providers to ensure sustainable production operation.

#### Scenario: Request Rate Limiting
- **WHEN** application makes requests to Meta APIs
- **THEN** provider SHALL enforce configurable rate limits (default: 150 requests/hour per app)
- **AND** implement token bucket algorithm with burst capacity
- **AND** provide HTTP status 429 responses with retry-after headers when limits exceeded

#### Scenario: Circuit Breaker Protection
- **WHEN** Meta API failure rate exceeds threshold (default: 50% over 5 minutes)
- **THEN** provider SHALL open circuit breaker automatically
- **AND** fallback to cached or mock data immediately
- **AND** attempt recovery after cool-down period (default: 5 minutes)
- **AND** log circuit breaker state transitions for monitoring

#### Scenario: API Retry with Backoff
- **WHEN** API call fails with transient error (timeout, 5xx server error)
- **THEN** provider SHALL retry with exponential backoff (starting 1s, max 30s)
- **AND** limit maximum retry attempts (default: 3)
- **AND** implement jitter to avoid thundering herd
- **AND** fail permanently after max retries exceeded

#### Scenario: Provider Health Monitoring
- **WHEN** provider health status is requested
- **THEN** provider SHALL report current rate limiting status
- **AND** include current request rate and remaining capacity
- **AND** indicate circuit breaker state (open/closed/half-open)
- **AND** provide cache hit/miss metrics when available