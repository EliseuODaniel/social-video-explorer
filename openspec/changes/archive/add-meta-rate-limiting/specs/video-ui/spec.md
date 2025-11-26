## MODIFIED Requirements

### Requirement: Rate Limiting Status Indicators
The system SHALL display real-time rate limiting status and usage information in the Streamlit interface.

#### Scenario: Rate Limiting Status Display
- **WHEN** user accesses the main interface
- **THEN** system SHALL show rate limiting status in sidebar
- **AND** display current request rate (requests/hour)
- **AND** show remaining requests until limit
- **AND** indicate rate limit status (Normal/Warning/Limited)

#### Scenario: Request Usage Counter
- **WHEN** user performs searches or requests
- **THEN** system SHALL update usage counter in real-time
- **AND** show visual indicator when approaching limits (>80%)
- **AND** display exact remaining requests
- **AND** reset counter when time window expires

#### Scenario: Cache Status Indicators
- **WHEN** search results are displayed
- **THEN** system SHALL show cache hit/miss indicators
- **AND** display cache efficiency percentage
- **AND** provide cache status icon (hit/miss/loading)
- **AND** show timestamp of cached data when available

#### Scenario: Rate Limit Warning Messages
- **WHEN** user approaches rate limit (>80% usage)
- **THEN** system SHALL display warning banner
- **AND** suggest waiting before new requests
- **AND** recommend using cached results
- **AND** provide estimated wait time until reset

### Requirement: Graceful Error Handling for Rate Limits
The system SHALL provide user-friendly error handling when rate limits are reached.

#### Scenario: Rate Limit Exceeded Messages
- **WHEN** rate limit is exceeded (HTTP 429)
- **THEN** system SHALL display friendly error message
- **AND** explain rate limit policy clearly
- **AND** suggest using cached results
- **AND** provide wait time estimate until next request
- **AND** maintain system stability during limit periods

#### Scenario: Service Unavailability Fallback
- **WHEN** Meta APIs are unavailable due to rate limiting
- **THEN** system SHALL automatically fallback to cached results
- **AND** display "Offline Mode" status indicator
- **AND** show timestamp of last successful data
- **AND** allow basic browsing of cached content

#### Scenario: Error Recovery Notification
- **WHEN** service recovers from rate limiting
- **THEN** system SHALL display success notification
- **AND** automatically refresh rate limit status
- **AND** re-enable normal search functionality
- **AND** clear any warning banners