## ADDED Requirements

### Requirement: Video Search Service
The system SHALL provide a centralized search service that can query multiple video providers and return normalized results with configurable limits and filters.

#### Scenario: Successful multi-provider search
- **WHEN** user performs video search with SearchParams including max_results=10
- **AND** multiple providers are available (Meta, YouTube, etc.)
- **THEN** search service SHALL query all enabled providers
- **AND** merge results respecting the max_results limit
- **AND** return normalized VideoResult objects with raw_payload from each provider

#### Scenario: Search with pagination
- **WHEN** user requests search with page parameter > 1
- **AND** provider supports pagination
- **THEN** search service SHALL fetch the specified page
- **AND** maintain result order and consistency across requests

#### Scenario: Provider rate limiting
- **WHEN** provider API returns rate limit exceeded
- **THEN** search service SHALL gracefully handle the error
- **AND** include provider availability status in response
- **AND** continue querying other available providers

#### Scenario: Result caching
- **WHEN** identical search query is performed within cache TTL
- **THEN** search service SHALL return cached results
- **AND** reduce API calls to rate-limited providers
- **AND** maintain cache invalidation for real-time searches

### Requirement: Search Parameters Validation
The system SHALL validate all search parameters and provide clear error messages for invalid inputs.

#### Scenario: Invalid max_results parameter
- **WHEN** user provides max_results outside allowed range (1-100)
- **THEN** system SHALL return validation error
- **AND** provide guidance on allowed range

#### Scenario: Date range validation
- **WHEN** user provides date range with end_date before start_date
- **THEN** system SHALL return validation error
- **AND** suggest corrected date range

### Requirement: Result Normalization
The system SHALL normalize video data from different providers into a consistent VideoResult format while preserving raw data.

#### Scenario: Meta video normalization
- **WHEN** Meta API returns video data with platform-specific fields
- **THEN** system SHALL map fields to VideoResult schema
- **AND** store complete raw API response in raw_payload field
- **AND** include source provider metadata

#### Scenario: YouTube video normalization
- **WHEN** YouTube API returns video data with different field names
- **THEN** system SHALL normalize to VideoResult schema
- **AND** handle missing optional fields gracefully
- **AND** preserve YouTube-specific data in raw_payload