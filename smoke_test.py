#!/usr/bin/env python3
"""Basic smoke test to verify the implementation works without external dependencies."""

import sys
import asyncio

def test_imports():
    """Test that all core modules can be imported."""
    try:
        from core.schemas import VideoResult, SearchParams, SearchResponse, VideoProvider
        from core.providers.base import BaseVideoProvider, ProviderCapabilities
        from core.providers.mock import MockProvider
        from core.providers.meta import MetaProvider
        from core.services.search_service import SearchService
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_schemas():
    """Test basic schema creation and validation."""
    try:
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

        print("✅ Schema creation successful")
        print(f"   - Video: {video.title} from {video.provider.value}")
        print(f"   - Params: '{params.query}' (max: {params.max_results})")
        return True
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_providers():
    """Test basic provider functionality."""
    try:
        from core.providers.mock import MockProvider
        from core.providers.meta import MetaProvider
        from core.schemas import VideoProvider

        # Test mock provider
        mock_provider = MockProvider()
        caps = mock_provider.get_capabilities()

        print("✅ Provider creation successful")
        print(f"   - Mock provider available: {mock_provider.is_available()}")
        print(f"   - Mock max results: {caps.max_results_per_search}")
        print(f"   - Mock provider type: {mock_provider.provider_type.value}")
        return True
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        return False

async def test_search_service():
    """Test basic search service functionality."""
    try:
        from core.services.search_service import SearchService
        from core.schemas import SearchParams

        service = SearchService()
        info = service.get_provider_info()

        print("✅ Search service creation successful")
        print(f"   - Total providers: {info['total_providers']}")
        print(f"   - Available providers: {[p.value for p in info['available_providers']]}")

        # Test search
        params = SearchParams(query="test video", max_results=5)
        response = await service.search(params)

        print(f"✅ Search successful: {len(response.results)} results")
        print(f"   - Provider used: {response.provider_used.value if response.provider_used else 'None'}")
        print(f"   - Mock mode: {response.is_mock_mode}")

        if response.results:
            first_result = response.results[0]
            print(f"   - First result: {first_result.title[:50]}...")

        return True
    except Exception as e:
        print(f"❌ Search service test failed: {e}")
        return False

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

    import os
    missing_files = []

    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

async def main():
    """Run all smoke tests."""
    print("🚀 Running Social Video Explorer Smoke Tests\n")

    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Schemas", test_schemas),
        ("Providers", test_providers),
        ("Search Service", test_search_service)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ❌ {test_name} failed")
        except Exception as e:
            print(f"   ❌ {test_name} crashed: {e}")

    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All smoke tests passed!")
        return True
    else:
        print("⚠️  Some tests failed - check implementation")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)