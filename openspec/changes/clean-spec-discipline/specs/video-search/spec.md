## MODIFIED Requirements

### Requirement: Basic Video Search Service
The system SHALL provide a centralized search service that can query a single video provider and return normalized results with basic configuration.

#### Scenario: Successful single-provider search
- **WHEN** user performs video search with SearchParams including max_results=10
- **AND** Meta provider is available
- **THEN** search service SHALL query the enabled provider
- **AND** respect the max_results limit
- **AND** return normalized VideoResult objects with raw_payload

#### Scenario: Mock mode search
- **WHEN** application runs without API credentials
- **THEN** search service SHALL use mock provider
- **AND** generate realistic sample video results
- **AND** simulate search behavior without external API calls

#### Scenario: Basic provider error handling
- **WHEN** provider call fails due to network or API errors
- **THEN** search service SHALL return appropriate error message
- **AND** include error details for debugging
- **AND** handle missing provider gracefully