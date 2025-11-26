## ADDED Requirements

### Requirement: Search Service Rate Awareness and Caching
The search service SHALL implement intelligent rate limiting awareness and caching to reduce API pressure and improve response times.

#### Scenario: Cache-First Search Strategy
- **WHEN** user performs search with query that has recent results
- **THEN** search service SHALL check cache before API calls
- **AND** return cached results immediately if available and valid
- **AND** update search_time_ms to reflect cache response time
- **AND** log cache hit for metrics

#### Scenario: Concurrent Search Coordination
- **WHEN** multiple concurrent searches are requested
- **THEN** search service SHALL coordinate rate limiting across providers
- **AND** respect per-provider rate limits simultaneously
- **AND** queue requests when providers are rate limited
- **AND** provide feedback about estimated wait time

#### Scenario: Search Result Caching
- **WHEN** search service receives results from providers
- **THEN** service SHALL cache results with appropriate TTL based on query type:
  - Hashtag searches: 1 hour TTL
  - User content searches: 30 minutes TTL
  - Trending/popular searches: 15 minutes TTL
- **AND** cache using query fingerprint as key
- **AND** include cache metadata (timestamp, provider, hit count)

#### Scenario: Rate Limit Error Handling
- **WHEN** provider returns rate limit exceeded (HTTP 429)
- **THEN** search service SHALL return cached results if available
- **AND** provide clear error message about rate limiting
- **AND** include estimated wait time for next request
- **AND** suggest using cached results meanwhile

#### Scenario: Search Quality with Rate Limits
- **WHEN** operating under rate limiting constraints
- **THEN** search service SHALL prioritize recent/frequent queries
- **AND** implement smart cache warming for popular searches
- **AND** maintain result quality while respecting rate limits
- **AND** provide transparent status about limitations