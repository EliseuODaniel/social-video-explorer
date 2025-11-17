"""Basic Streamlit UI for Social Video Explorer.

This module provides a simple web interface for searching and displaying videos
from multiple social platforms.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

import streamlit as st

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.search_service import SearchService
from core.schemas import SearchParams, VideoResult, VideoProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Social Video Explorer",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def initialize_search_service() -> SearchService:
    """Initialize and return the search service.

    Returns:
        Configured SearchService instance
    """
    # Load configuration from environment variables
    config = {}
    if os.getenv('META_ACCESS_TOKEN'):
        config['meta'] = {
            'access_token': os.getenv('META_ACCESS_TOKEN')
        }

    return SearchService(config)


def render_search_form(search_service: SearchService) -> tuple[bool, SearchParams | None]:
    """Render the search form and handle user input.

    Args:
        search_service: Configured search service

    Returns:
        Tuple of (should_search, search_params)
    """
    st.header("🔍 Video Search")

    with st.form("search_form"):
        # Search query
        query = st.text_input(
            "Search for videos:",
            placeholder="Enter keywords to search for videos...",
            help="Search across multiple video platforms for matching content"
        )

        # Search parameters
        col1, col2 = st.columns(2)
        with col1:
            max_results = st.slider(
                "Maximum results:",
                min_value=1,
                max_value=50,
                value=10,
                help="Maximum number of results to return"
            )

        with col2:
            # Provider selection (for now, show available providers)
            available_providers = search_service.get_available_providers()
            if VideoProvider.MOCK in available_providers:
                default_provider = VideoProvider.MOCK
            elif available_providers:
                default_provider = available_providers[0]
            else:
                default_provider = None

            provider_options = [p.value for p in available_providers] if available_providers else ["Mock"]
            selected_provider = st.selectbox(
                "Provider:",
                options=provider_options,
                index=0 if provider_options else 0,
                help="Select video provider to search"
            )

        # Submit button
        submitted = st.form_submit_button("Search Videos", type="primary")

        if submitted and not query.strip():
            st.error("Please enter a search query")
            return False, None

        if submitted and query.strip():
            try:
                # Create search parameters
                search_params = SearchParams(
                    query=query.strip(),
                    max_results=max_results,
                    provider=VideoProvider(selected_provider) if selected_provider != "Mock" else None
                )
                return True, search_params
            except Exception as e:
                st.error(f"Invalid search parameters: {str(e)}")
                return False, None

    return False, None


def render_provider_status(search_service: SearchService):
    """Render provider status information in sidebar.

    Args:
        search_service: Configured search service
    """
    st.sidebar.header("📊 Provider Status")

    provider_info = search_service.get_provider_info()

    for provider_name, info in provider_info["provider_details"].items():
        with st.sidebar.expander(f"{provider_name.upper()}"):
            if "error" in info:
                st.error(f"❌ Error: {info['error']}")
            else:
                is_available = info.get("is_available", False)
                is_configured = info.get("is_configured", False)

                if is_available and is_configured:
                    st.success("✅ Available and configured")
                elif is_available:
                    st.warning("⚠️ Available but not configured")
                else:
                    st.error("❌ Not available")

                st.write(f"Max results: {info.get('max_results', 'Unknown')}")

                if not is_configured:
                    setup_instructions = info.get("setup_instructions")
                    if setup_instructions:
                        with st.expander("Setup Instructions"):
                            st.text(setup_instructions)


def render_results(response):
    """Render search results in a grid layout.

    Args:
        response: SearchResponse with video results
    """
    if not response.results:
        st.info("No videos found. Try different search terms or check provider configuration.")
        return

    st.header(f"📹 Found {len(response.results)} videos")

    if response.is_mock_mode:
        st.info("🎭 Showing results from mock provider - configure real API credentials for live data")

    # Display results in columns (3 per row)
    cols_per_row = 3

    for i in range(0, len(response.results), cols_per_row):
        cols = st.columns(cols_per_row)

        for j, video in enumerate(response.results[i:i + cols_per_row]):
            with cols[j]:
                render_video_card(video)


def render_video_card(video: VideoResult):
    """Render a single video result card.

    Args:
        video: VideoResult object to display
    """
    with st.container():
        # Thumbnail
        if video.thumbnail_url:
            st.image(video.thumbnail_url, use_column_width=True)
        else:
            st.image("https://picsum.photos/320/180?random=" + video.video_id, use_column_width=True)

        # Title and metadata
        st.subheader(video.title, help=f"Provider: {video.provider.value}")

        # Author and stats
        if video.author:
            st.write(f"👤 {video.author}")

        # Engagement metrics (if available)
        metrics = []
        if video.view_count:
            metrics.append(f"👁️ {video.view_count:,}")
        if video.like_count:
            metrics.append(f"👍 {video.like_count:,}")
        if video.comment_count:
            metrics.append(f"💬 {video.comment_count:,}")

        if metrics:
            st.write(" | ".join(metrics))

        # Duration
        if video.duration_seconds:
            minutes, seconds = divmod(video.duration_seconds, 60)
            st.write(f"⏱️ {minutes}:{seconds:02d}")

        # Published date
        if video.published_at:
            st.write(f"📅 {video.published_at.strftime('%Y-%m-%d')}")

        # URL
        if video.url:
            st.markdown(f"[🔗 Watch Video]({video.url})")


def render_error(error_message: str):
    """Render error message to user.

    Args:
        error_message: Error message to display
    """
    st.error(f"❌ {error_message}")
    st.write("Please check your search parameters and try again.")


async def main():
    """Main application entry point."""
    setup_page_config()

    st.title("🎥 Social Video Explorer")
    st.markdown("Search and explore videos from multiple social media platforms")

    # Initialize search service
    try:
        search_service = initialize_search_service()
    except Exception as e:
        st.error(f"Failed to initialize search service: {str(e)}")
        return

    # Render provider status
    render_provider_status(search_service)

    # Render search form
    should_search, search_params = render_search_form(search_service)

    # Perform search if requested
    if should_search and search_params:
        with st.spinner("Searching for videos..."):
            try:
                response = await search_service.search(search_params)
                render_results(response)
            except Exception as e:
                logger.error(f"Search error: {e}")
                render_error(str(e))


def run_async(coro):
    """Run async coroutine in sync context.

    Args:
        coro: Coroutine to run
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == "__main__":
    run_async(main())