#!/usr/bin/env python3
"""Custom test runner that doesn't require external dependencies."""

import sys
import os
import traceback
import asyncio

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_test(test_name, test_func):
    """Run a single test and return success status."""
    print(f"🧪 Running {test_name}...")
    try:
        if asyncio.iscoroutinefunction(test_func):
            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(test_func())
            finally:
                loop.close()
        else:
            # Run sync test
            test_func()

        print(f"✅ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name} FAILED: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_imports():
    """Test that all modules can be imported successfully."""
    from core.schemas import VideoResult, SearchParams, VideoProvider
    from core.providers.base import BaseVideoProvider, ProviderCapabilities
    from core.providers.mock import MockProvider
    from core.providers.meta import MetaProvider
    from core.services.search_service import SearchService
    return True

def test_schemas_creation():
    """Test basic schema creation and validation."""
    from core.schemas import VideoResult, SearchParams, VideoProvider

    # Test VideoResult creation
    video = VideoResult(
        video_id="test_123",
        title="Test Video",
        provider=VideoProvider.MOCK,
        url="https://example.com/video/test_123"
    )

    # Test SearchParams creation
    params = SearchParams(query="test", max_results=10)

    # Basic validation
    assert video.video_id == "test_123"
    assert video.provider == VideoProvider.MOCK
    assert params.query == "test"
    assert params.max_results == 10

    return True

def test_provider_creation():
    """Test provider creation and basic functionality."""
    from core.providers.mock import MockProvider
    from core.providers.meta import MetaProvider
    from core.schemas import VideoProvider

    # Test mock provider
    mock_provider = MockProvider()
    caps = mock_provider.get_capabilities()

    assert mock_provider.provider_type == VideoProvider.MOCK
    assert mock_provider.is_available() == True
    assert caps.supports_search == True
    assert caps.requires_authentication == False

    # Test meta provider
    meta_provider = MetaProvider()
    assert meta_provider.provider_type == VideoProvider.META

    # Test setup instructions
    mock_info = mock_provider.get_config_info()
    meta_info = meta_provider.get_config_info()

    assert "setup_instructions" in mock_info
    assert "setup_instructions" in meta_info

    return True

async def test_search_service():
    """Test search service functionality."""
    from core.services.search_service import SearchService
    from core.schemas import SearchParams, VideoProvider

    service = SearchService()

    # Test provider info
    info = service.get_provider_info()
    assert "total_providers" in info
    assert "available_providers" in info
    assert "mock" in info["provider_details"]

    # Test search with mock provider
    params = SearchParams(query="test video", max_results=5)
    response = await service.search(params)

    assert response.results is not None
    assert len(response.results) <= 5
    assert response.total_results == len(response.results)
    assert response.provider_used == VideoProvider.MOCK
    assert response.is_mock_mode == True

    # Validate result structure
    if response.results:
        video = response.results[0]
        assert video.video_id is not None
        assert video.title is not None
        assert video.provider == VideoProvider.MOCK
        assert video.url is not None
        assert video.raw_payload is not None

    return True

def test_validation():
    """Test input validation."""
    from core.schemas import SearchParams, VideoProvider
    from pydantic import ValidationError

    # Test valid params
    params = SearchParams(query="valid", max_results=25)
    assert params.query == "valid"
    assert params.max_results == 25

    # Test invalid params
    try:
        SearchParams(query="", max_results=100)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected

    try:
        SearchParams(query="test", max_results=0)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected

    return True

def test_file_structure():
    """Test that all required files exist."""
    required_files = [
        "core/schemas.py",
        "core/providers/base.py",
        "core/providers/meta.py",
        "core/providers/mock.py",
        "core/services/search_service.py",
        "ui/streamlit_app.py",
        "requirements.txt",
        "pyproject.toml",
        ".gitignore",
        ".env.example",
        "README.md"
    ]

    for file_path in required_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Required file missing: {file_path}")

    return True

async def run_all_tests():
    """Run all tests and return overall success status."""
    print("🚀 Running Custom Test Suite for Social Video Explorer\n")

    tests = [
        ("Import Tests", test_imports),
        ("Schema Creation Tests", test_schemas_creation),
        ("Provider Creation Tests", test_provider_creation),
        ("Search Service Tests", test_search_service),
        ("Validation Tests", test_validation),
        ("File Structure Tests", test_file_structure)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1

    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        print("✅ Implementation is working correctly")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)