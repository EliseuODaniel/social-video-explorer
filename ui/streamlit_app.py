"""
Streamlit UI for Social Video Explorer

This module provides a web interface for searching and exploring
social media video content across multiple platforms.
"""

import os
import sys
import asyncio
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.search_service import SearchService
from core.schemas import SearchParams, Platform, MediaType, VideoResult


# Configure Streamlit page
st.set_page_config(
    page_title="Social Video Explorer",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .status-indicator {
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-production {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .status-mock {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .video-result {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .platform-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .platform-instagram {
        background-color: #E4405F;
        color: white;
    }
    .platform-facebook {
        background-color: #1877F2;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_search_service():
    """Initialize the search service."""
    if "search_service" not in st.session_state:
        try:
            st.session_state.search_service = SearchService()
        except Exception as e:
            st.error(f"Failed to initialize search service: {e}")
            st.session_state.search_service = None
    return st.session_state.search_service


def show_production_status(search_service: SearchService):
    """Display production mode status and provider information."""
    st.markdown("### 📊 System Status")

    try:
        # Get system health asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        system_health = loop.run_until_complete(search_service.get_system_health())
        loop.close()

        # Main status indicator
        if search_service.production_mode:
            if system_health.is_healthy:
                st.markdown(
                    '<div class="status-indicator status-production">'
                    "🟢 Production Mode - Meta APIs Active</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="status-indicator status-error">'
                    "🔴 Production Mode - API Issues Detected</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="status-indicator status-mock">'
                "🟡 Mock Mode - Using Sample Data</div>",
                unsafe_allow_html=True,
            )

        # OAuth status
        oauth_status = search_service.get_oauth_status()
        if oauth_status.get("oauth_configured"):
            if oauth_status.get("app_token_valid"):
                st.info("✅ Meta Authentication Valid")
            else:
                st.warning("⚠️ Meta Authentication Issues")
        else:
            st.info("ℹ️ OAuth not configured (Mock mode)")

        # Provider details
        if system_health.providers:
            st.markdown("#### Provider Details")
            for provider in system_health.providers:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{provider.name}**")
                with col2:
                    if provider.is_healthy:
                        st.success("🟢 Healthy")
                    else:
                        st.error("🔴 Unhealthy")
                with col3:
                    if provider.response_time_ms:
                        st.write(f"{provider.response_time_ms}ms")

    except Exception as e:
        st.error(f"Failed to get system status: {e}")


def show_search_form():
    """Display the search form."""
    st.markdown("### 🔍 Search Social Media")

    with st.form("search_form"):
        # Search query
        query = st.text_input(
            "Search Query",
            placeholder="Enter hashtag or keyword (e.g., travel, fitness, tech)",
            help="Search for content by hashtag or keyword",
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            platform = st.selectbox(
                "Platform",
                options=[
                    ("All Platforms", Platform.ALL),
                    ("Meta (FB + Instagram)", Platform.META),
                    ("Instagram", Platform.INSTAGRAM),
                    ("Facebook", Platform.FACEBOOK),
                ],
                format_func=lambda x: x[0],
            )[1]

        with col2:
            media_type = st.selectbox(
                "Media Type",
                options=[
                    ("All Media", MediaType.ALL),
                    ("Videos", MediaType.VIDEO),
                    ("Photos", MediaType.PHOTO),
                    ("Reels", MediaType.REEL),
                ],
                format_func=lambda x: x[0],
            )[1]

        with col3:
            max_results = st.slider(
                "Max Results", min_value=5, max_value=50, value=20, step=5
            )

        col4, col5 = st.columns(2)

        with col4:
            sort_by = st.selectbox(
                "Sort By",
                options=["recent", "popular", "relevant"],
                format_func=lambda x: x.title(),
            )

        submitted = st.form_submit_button("🔍 Search", use_container_width=True)

        return {
            "query": query,
            "platform": platform,
            "media_type": media_type,
            "max_results": max_results,
            "sort_by": sort_by,
            "submitted": submitted,
        }


def display_video_results(results: List[VideoResult]):
    """Display search results in a formatted way."""
    if not results:
        st.info("No results found. Try adjusting your search criteria.")
        return

    st.markdown(f"### 📺 Found {len(results)} Results")

    for i, result in enumerate(results):
        with st.container():
            # Platform badge - handle both enum and string values
            platform_value = result.platform.value if hasattr(result.platform, 'value') else str(result.platform)
            platform_class = f"platform-{platform_value}"
            st.markdown(
                f'<span class="platform-badge {platform_class}">{platform_value.upper()}</span>',
                unsafe_allow_html=True,
            )

            # Title and metadata
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{result.title}**")
                st.caption(f"Posted: {result.created_at.strftime('%Y-%m-%d %H:%M')}")
                if result.media_type:
                    media_type_value = result.media_type.value if hasattr(result.media_type, 'value') else str(result.media_type)
                    st.caption(f"Media: {media_type_value}")

            with col2:
                # Engagement metrics
                if result.like_count or result.comment_count:
                    st.write("👍", result.like_count or 0)
                    st.write("💬", result.comment_count or 0)

            # Media display
            if result.thumbnail_url:
                try:
                    st.image(result.thumbnail_url, width=300)
                except Exception:
                    st.warning("⚠️ Could not load thumbnail")

            # Links
            col1, col2 = st.columns(2)

            with col1:
                if result.url:
                    st.markdown(f"[🔗 View Original]({result.url})")

            with col2:
                if st.button(f"📋 Details", key=f"details_{i}"):
                    with st.expander("Raw Details", expanded=True):
                        st.json(result.raw_payload)

            st.divider()


def show_search_summary(response):
    """Display search summary information."""
    if not response:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Results Found", response.total_found)

    with col2:
        st.metric("Search Time", f"{response.search_time_ms}ms")

    with col3:
        st.metric("Platforms", len(response.platforms_searched))

    with col4:
        st.metric(
            "Query",
            (
                response.query_used[:20] + "..."
                if len(response.query_used) > 20
                else response.query_used
            ),
        )

    # Errors
    if response.errors:
        st.markdown("#### ⚠️ Search Errors")
        for error in response.errors:
            st.error(error)


def main():
    """Main application entry point."""
    st.markdown("# 🎥 Social Video Explorer")
    st.markdown("Search and explore video content across social media platforms")

    # Initialize search service
    search_service = initialize_search_service()
    if not search_service:
        st.error("Failed to initialize application. Please check configuration.")
        return

    # Sidebar with status information
    with st.sidebar:
        show_production_status(search_service)

        # Configuration info
        st.markdown("---")
        st.markdown("### ℹ️ Configuration")
        production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
        st.write(f"Mode: {'Production' if production_mode else 'Mock'}")

        if production_mode:
            if os.getenv("META_APP_ID"):
                st.success("✅ Meta App ID configured")
            else:
                st.error("❌ Meta App ID missing")
        else:
            st.info("💡 Set PRODUCTION_MODE=true to use real APIs")

    # Main content area
    search_params = show_search_form()

    if search_params["submitted"] and search_params["query"]:
        try:
            # Create search parameters
            params = SearchParams(
                query=search_params["query"],
                platform=search_params["platform"],
                media_type=search_params["media_type"],
                max_results=search_params["max_results"],
                sort_by=search_params["sort_by"],
            )

            # Show loading spinner
            with st.spinner(
                f"Searching {search_params['platform'].value} for '{search_params['query']}'..."
            ):
                # Perform search asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(search_service.search(params))
                loop.close()

            # Show search summary
            show_search_summary(response)

            # Display results
            display_video_results(response.results)

        except Exception as e:
            st.error(f"Search failed: {e}")
            st.exception(e)

    elif search_params["submitted"]:
        st.warning("Please enter a search query")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
        Social Video Explorer MVP - Meta Provider Integration
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
