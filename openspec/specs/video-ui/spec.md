# Video UI Capability

This specification defines the Streamlit-based user interface for the Social Video Explorer system.

## Requirements

### Requirement: Basic Streamlit Video Search Interface
The system SHALL provide a basic web-based user interface using Streamlit for searching and displaying video results.

#### Scenario: Basic search form interaction
- **WHEN** user accesses the main Streamlit page
- **THEN** system SHALL display search input field
- **AND** show basic search parameters (query, max_results)
- **AND** provide clear search button with loading state

#### Scenario: Basic search execution
- **WHEN** user submits search form with valid parameters
- **THEN** system SHALL show loading spinner during search
- **AND** call search service with provided parameters
- **AND** handle basic errors with user-friendly messages

#### Scenario: Basic results grid display
- **WHEN** search service returns video results
- **THEN** system SHALL display results in simple grid layout
- **AND** show basic video information (title, thumbnail, provider)
- **AND** display results in a scrollable list

### Requirement: Basic Video Result Display
The system SHALL display video results in a simple card format with essential metadata.

#### Scenario: Basic video card display
- **WHEN** displaying a single video result
- **THEN** card SHALL show video thumbnail
- **AND** display title and basic metadata
- **AND** include provider source information

#### Scenario: Mock mode indication
- **WHEN** application runs in demo mode
- **THEN** system SHALL display demo mode indicator
- **AND** show that results are sample data
- **AND** provide guidance for real API setup

### Requirement: Basic Mock Service Integration
The system SHALL include mock service mode for demonstration without requiring real API credentials.

#### Scenario: Mock search results
- **WHEN** application runs without API keys
- **THEN** system SHALL use mock search service
- **AND** generate sample video data
- **AND** display clear demo mode indicators

#### Scenario: Basic provider status
- **WHEN** providers are unavailable due to missing credentials
- **THEN** system SHALL show basic provider status
- **AND** provide simple setup instructions
- **AND** enable mock mode automatically

### Requirement: Basic Error Handling
The system SHALL provide clear error messages for basic operations.

#### Scenario: Search error handling
- **WHEN** search fails due to basic errors
- **THEN** system SHALL display user-friendly error message
- **AND** provide simple retry guidance

#### Scenario: No results scenario
- **WHEN** search returns zero results
- **THEN** system SHALL display "no results" message
- **AND** suggest trying different search terms