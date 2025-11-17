# Delta: Video UI Specification

## Current State
Streamlit UI operates in demo mode only, shows sample mock data, has no production status indicators, and lacks OAuth integration feedback.

## Target State
Production-aware UI with Meta provider status indicators, OAuth authentication feedback, real API data display, and clear production vs mock mode distinction.

## Changes Required

### 1. Production Mode Status Bar

**Current header**:
```python
st.title("Social Video Explorer")
st.write("Explore content from multiple social platforms")
```

**Target header with status**:
```python
def render_app_header():
    """Render app header with production status"""
    production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("Social Video Explorer")

    with col2:
        if production_mode:
            st.success("🟢 Production Mode")
        else:
            st.warning("🟡 Mock Mode")

def render_status_sidebar():
    """Render detailed status information in sidebar"""
    st.sidebar.markdown("## System Status")

    production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

    # Mode indicator
    if production_mode:
        st.sidebar.success("✅ Production APIs Active")
    else:
        st.sidebar.info("ℹ️ Demo Mode - Sample Data")

    # OAuth status (when in production)
    if production_mode:
        oauth_status = check_oauth_status()
        if oauth_status['valid']:
            st.sidebar.success("✅ Meta Authenticated")
            st.sidebar.caption(f"Token expires: {oauth_status['expires_at']}")
        else:
            st.sidebar.error("❌ Meta Authentication Required")
            if st.sidebar.button("Connect to Meta"):
                initiate_oauth_flow()

    # Provider health
    provider_health = asyncio.run(check_provider_health())
    st.sidebar.markdown("### Provider Health")
    for provider, status in provider_health.items():
        if status['status'] == 'healthy':
            st.sidebar.success(f"✅ {provider.title()}")
        else:
            st.sidebar.error(f"❌ {provider.title()}")
```

### 2. Enhanced Search Interface

**Current search form**:
```python
query = st.text_input("Search query")
platform = st.selectbox("Platform", ["mock", "meta"])
max_results = st.slider("Max results", 5, 50, 20)

if st.button("Search"):
    # Basic search execution
    results = search_service.search(SearchParams(query, platform, max_results))
    display_results(results)
```

**Target enhanced search interface**:
```python
def render_search_interface():
    """Enhanced search interface with production awareness"""
    st.markdown("## Search Content")

    production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

    # Search parameters
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        query = st.text_input(
            "Search query",
            placeholder="Enter hashtags, keywords, or content..."
        )

    with col2:
        platform = st.selectbox(
            "Platform",
            options=["meta", "instagram", "facebook", "mock"],
            help="Meta platforms use real APIs in production mode"
        )

    with col3:
        max_results = st.slider("Results", 5, 50, 20)

    # Advanced options (collapsible)
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            include_fallback = st.checkbox(
                "Include fallback results",
                value=True,
                help="Use mock data if production APIs fail"
            )

            search_timeout = st.slider(
                "Timeout (seconds)",
                5, 60, 30
            )

        with col2:
            if production_mode and platform in ["meta", "instagram", "facebook"]:
                hashtag_filter = st.text_input(
                    "Hashtag filter",
                    placeholder="e.g., travel, food, tech",
                    help="Filter by specific hashtags"
                )

                media_type = st.selectbox(
                    "Media type",
                    ["all", "video", "photo"],
                    help="Filter by media type (Meta platforms only)"
                )

    # Search button with loading state
    search_disabled = not query.strip()

    if st.button("🔍 Search", disabled=search_disabled, type="primary"):
        if production_mode and platform in ["meta", "instagram", "facebook"]:
            # Show production search warning
            st.info("🔄 Searching with real Meta APIs...")
        else:
            st.info("🔄 Searching with sample data...")

        # Execute search with progress indicator
        with st.spinner("Searching..."):
            try:
                results = execute_search(
                    query=query,
                    platform=platform,
                    max_results=max_results,
                    include_fallback=include_fallback,
                    timeout=search_timeout,
                    hashtag_filter=hashtag_filter if production_mode else None,
                    media_type=media_type if production_mode and media_type != "all" else None
                )

                display_results(results, query, platform)

            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
                if production_mode:
                    st.info("💡 Try again or switch to mock mode for testing")
```

### 3. Enhanced Results Display

**Current results display**:
```python
def display_results(results):
    st.write(f"Found {len(results)} results:")
    for result in results:
        st.write(f"- {result.title} ({result.platform})")
```

**Target enhanced results display**:
```python
def display_results(results: List[VideoResult], query: str, platform: str):
    """Enhanced results display with production data awareness"""
    if not results:
        st.warning("No results found")
        return

    production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

    # Results summary
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.write(f"**{len(results)} results** for '{query}' from {platform}")

    with col2:
        if production_mode and platform in ["meta", "instagram", "facebook"]:
            st.success("🔴 Live Data")
        else:
            st.info("📋 Sample Data")

    with col3:
        if st.button("📥 Export Results"):
            export_results_to_csv(results)

    # Results grid
    for i, result in enumerate(results):
        with st.container():
            col1, col2 = st.columns([1, 3])

            with col1:
                if result.thumbnail_url:
                    st.image(result.thumbnail_url, width=150)
                else:
                    st.image("https://via.placeholder.com/150x150.png?placeholder=No+Image", width=150)

            with col2:
                # Title and platform
                st.markdown(f"### {result.title}")

                platform_badge = get_platform_badge(result.platform)
                st.markdown(f"{platform_badge} • {format_date(result.created_at)}")

                # URL and actions
                st.markdown(f"[🔗 View Original]({result.url})")

                # Additional metadata for production data
                if production_mode and result.platform in ["instagram", "facebook"]:
                    if hasattr(result, 'engagement') and result.engagement:
                        engagement_text = f"💬 {result.engagement.get('likes', 0)} likes • {result.engagement.get('comments', 0)} comments"
                        st.caption(engagement_text)

                # Raw data toggle
                with st.expander(f"Raw data for {result.platform.upper()} post"):
                    st.json(result.raw_payload)

            st.divider()

def get_platform_badge(platform: str) -> str:
    """Get platform badge styling"""
    badges = {
        "instagram": "📷 Instagram",
        "facebook": "📘 Facebook",
        "meta": "🌐 Meta",
        "mock": "🧪 Mock"
    }
    return badges.get(platform.lower(), f"🔹 {platform.title()}")
```

### 4. OAuth Integration Flow

**Add OAuth authentication handling**:
```python
def handle_oauth_callback():
    """Handle OAuth callback from Meta"""
    query_params = st.query_params

    if 'code' in query_params:
        # Exchange authorization code for access token
        auth_code = query_params['code']

        try:
            oauth_client = MetaOAuth2Client()
            token_info = await oauth_client.get_user_token(auth_code)

            # Store token securely
            store_oauth_token(token_info)

            st.success("✅ Successfully connected to Meta!")
            st.info("You can now search real content from Instagram and Facebook")

            # Clear URL parameters
            st.query_params.clear()

        except Exception as e:
            st.error(f"❌ Authentication failed: {str(e)}")
            st.info("Please try again or contact support")

def initiate_oauth_flow():
    """Start OAuth authentication flow"""
    oauth_client = MetaOAuth2Client()
    auth_url, state = oauth_client.get_authorization_url()

    # Store state for CSRF protection
    st.session_state['oauth_state'] = state

    # Redirect to Meta authorization
    st.markdown(f'''
    <script>
        window.location.href = "{auth_url}";
    </script>
    ''', unsafe_allow_html=True)

def check_oauth_status() -> Dict[str, Any]:
    """Check current OAuth authentication status"""
    try:
        oauth_client = MetaOAuth2Client()
        token_info = oauth_client.get_stored_token()

        if not token_info:
            return {'valid': False, 'error': 'No token found'}

        if oauth_client.is_token_expired(token_info):
            return {'valid': False, 'error': 'Token expired'}

        return {
            'valid': True,
            'expires_at': token_info.get('expires_at'),
            'token_type': token_info.get('token_type')
        }

    except Exception as e:
        return {'valid': False, 'error': str(e)}
```

### 5. Error Handling and User Feedback

**Enhanced error handling**:
```python
def display_search_error(error: Exception, platform: str):
    """Display user-friendly error messages"""
    production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

    if isinstance(error, MetaAuthError):
        st.error("❌ Meta Authentication Required")
        st.info("Please connect your Meta account in the sidebar to search real content")

    elif isinstance(error, MetaRateLimitError):
        st.error("⏰ Meta API Rate Limit Exceeded")
        st.info("Please wait a moment before trying again, or switch to mock mode")

    elif isinstance(error, NetworkError):
        st.error("🌐 Network Connection Failed")
        if production_mode:
            st.info("Check your internet connection or try mock mode for testing")
        else:
            st.info("Please check your internet connection")

    elif isinstance(error, SearchTimeoutError):
        st.error("⏱️ Search Timeout")
        st.info("Try increasing the timeout setting or reducing the number of results")

    else:
        st.error(f"❌ Unexpected Error: {str(error)}")
        if production_mode:
            st.info("Try switching to mock mode to continue using the application")
```

### 6. Performance and Metrics Display

**Add performance metrics**:
```python
def display_search_metrics(search_time: float, results_count: int, platform: str):
    """Display search performance metrics"""
    with st.expander("📊 Search Metrics"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Response Time", f"{search_time:.2f}s")

        with col2:
            st.metric("Results Found", results_count)

        with col3:
            st.metric("Results/Second", f"{results_count/search_time:.1f}")

        # Platform-specific info
        production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
        if production_mode and platform in ["meta", "instagram", "facebook"]:
            st.caption(f"🔴 Live Meta APIs • Real data from {platform.title()}")
        else:
            st.caption(f"📋 Mock Data • Sample results for testing")
```

## Configuration Updates

### Environment Variables
```bash
# .env.example additions
PRODUCTION_MODE=false                    # UI behavior changes based on this
SHOW_RAW_DATA_TOGGLE=true               # Allow users to see raw API responses
EXPORT_RESULTS_ENABLED=true            # Enable CSV export functionality
DISPLAY_PERFORMANCE_METRICS=true        # Show search performance metrics
OAUTH_CALLBACK_PATH=/oauth/callback     # OAuth redirect endpoint
```

### UI Configuration
```python
# config/ui_config.py
UI_CONFIG = {
    'show_raw_data': os.getenv('SHOW_RAW_DATA_TOGGLE', 'true').lower() == 'true',
    'export_enabled': os.getenv('EXPORT_RESULTS_ENABLED', 'true').lower() == 'true',
    'show_metrics': os.getenv('DISPLAY_PERFORMANCE_METRICS', 'true').lower() == 'true',
    'theme': 'light',  # or 'dark'
    'results_per_page': 20,
    'image_placeholder': "https://via.placeholder.com/150x150.png?placeholder=No+Image"
}
```

## Testing Strategy

### Unit Tests
- Production mode detection and UI behavior
- OAuth status checking and display
- Error message rendering for different failure types
- Platform badge generation and styling

### Integration Tests
- End-to-end search workflow with production APIs
- OAuth flow simulation and callback handling
- Fallback behavior UI feedback
- Export functionality testing

### UI/UX Tests
- Responsive design on different screen sizes
- Loading states and progress indicators
- Error message clarity and actionability
- Production vs mock mode visual distinction

## Migration Path

### Phase 1: Non-Breaking Visual Updates
1. Add production mode status bar
2. Enhanced search form layout
3. Improve results display styling

### Phase 2: Interactive Features
1. OAuth integration and status display
2. Provider health monitoring
3. Error handling improvements

### Phase 3: Advanced Features
1. Export functionality
2. Performance metrics display
3. Raw data inspection toggle

## Accessibility Considerations

- High contrast mode support
- Screen reader compatibility for status indicators
- Keyboard navigation for search interface
- Clear error messages with actionable guidance
- Alternative text for platform icons and badges

## Security Considerations

- OAuth state parameter validation
- Token storage in secure session state
- URL parameter sanitization
- XSS protection for raw data display
- CSRF protection for OAuth flows