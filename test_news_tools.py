#!/usr/bin/env python3
"""
Unit tests for News Tools - validates all 5 news management tools.

This script tests:
1. Pydantic input validation
2. Formatting functions
3. Tool functionality (without actual API calls)
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_pydantic_models():
    """Test Pydantic input validation for news tools."""
    print("\n" + "=" * 70)
    print("Test 1: Pydantic Model Validation")
    print("=" * 70)
    
    from src.tools.news import CreateNewsInput, UpdateNewsInput
    
    # Test 1.1: Valid CreateNewsInput
    print("\n[1.1] Testing CreateNewsInput - Valid")
    try:
        valid_input = CreateNewsInput(
            project_id=1,
            title="Test News",
            summary="This is a test summary",
            description="# Test\n\nThis is a test description"
        )
        assert valid_input.project_id == 1
        assert valid_input.title == "Test News"
        print("✅ PASSED: Valid input accepted")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 1.2: Invalid CreateNewsInput - missing required fields
    print("\n[1.2] Testing CreateNewsInput - Missing required fields")
    try:
        CreateNewsInput(
            project_id=1,
            title="Test"
            # Missing summary and description
        )
        print("❌ FAILED: Should have raised validation error")
        return False
    except Exception as e:
        print(f"✅ PASSED: Validation error caught: {type(e).__name__}")
    
    # Test 1.3: Invalid CreateNewsInput - title too long
    print("\n[1.3] Testing CreateNewsInput - Title too long")
    try:
        CreateNewsInput(
            project_id=1,
            title="A" * 256,  # More than 255 chars
            summary="Test",
            description="Test"
        )
        print("❌ FAILED: Should have raised validation error for long title")
        return False
    except Exception as e:
        print(f"✅ PASSED: Validation error caught: {type(e).__name__}")
    
    # Test 1.4: Invalid CreateNewsInput - invalid project_id
    print("\n[1.4] Testing CreateNewsInput - Invalid project_id")
    try:
        CreateNewsInput(
            project_id=0,  # Must be > 0
            title="Test",
            summary="Test",
            description="Test"
        )
        print("❌ FAILED: Should have raised validation error for project_id")
        return False
    except Exception as e:
        print(f"✅ PASSED: Validation error caught: {type(e).__name__}")
    
    # Test 1.5: Valid UpdateNewsInput
    print("\n[1.5] Testing UpdateNewsInput - Valid")
    try:
        valid_input = UpdateNewsInput(
            news_id=5,
            title="Updated Title"
        )
        assert valid_input.news_id == 5
        assert valid_input.title == "Updated Title"
        assert valid_input.summary is None
        print("✅ PASSED: Valid update input accepted")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 1.6: Valid UpdateNewsInput - partial update
    print("\n[1.6] Testing UpdateNewsInput - Partial update")
    try:
        valid_input = UpdateNewsInput(
            news_id=10,
            description="New description only"
        )
        assert valid_input.news_id == 10
        assert valid_input.title is None
        assert valid_input.description == "New description only"
        print("✅ PASSED: Partial update input accepted")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    print("\n✅ All Pydantic validation tests PASSED")
    return True


def test_formatting_functions():
    """Test news formatting functions."""
    print("\n" + "=" * 70)
    print("Test 2: Formatting Functions")
    print("=" * 70)
    
    from src.utils.formatting import format_news_list, format_news_detail
    
    # Test 2.1: format_news_list with empty list
    print("\n[2.1] Testing format_news_list - Empty list")
    try:
        result = format_news_list([])
        assert "No news entries found" in result
        print("✅ PASSED: Empty list handled correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2.2: format_news_list with single item
    print("\n[2.2] Testing format_news_list - Single item")
    try:
        test_news = [{
            "id": 1,
            "title": "Test News Entry",
            "summary": "This is a test summary",
            "createdAt": "2025-12-11T10:30:00.000Z",
            "_links": {
                "project": {"title": "Test Project"},
                "author": {"title": "John Doe"}
            }
        }]
        result = format_news_list(test_news)
        assert "📰 News List" in result
        assert "Test News Entry" in result
        assert "Test Project" in result
        assert "John Doe" in result
        assert "2025-12-11" in result
        print("✅ PASSED: Single item formatted correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2.3: format_news_list with multiple items
    print("\n[2.3] Testing format_news_list - Multiple items")
    try:
        test_news = [
            {
                "id": 1,
                "title": "News 1",
                "summary": "Summary 1",
                "createdAt": "2025-12-11T10:00:00.000Z",
                "_links": {
                    "project": {"title": "Project A"},
                    "author": {"title": "User 1"}
                }
            },
            {
                "id": 2,
                "title": "News 2",
                "summary": "Summary 2",
                "createdAt": "2025-12-10T15:00:00.000Z",
                "_links": {
                    "project": {"title": "Project B"},
                    "author": {"title": "User 2"}
                }
            }
        ]
        result = format_news_list(test_news)
        assert "2 items" in result
        assert "News 1" in result
        assert "News 2" in result
        print("✅ PASSED: Multiple items formatted correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2.4: format_news_list with long summary
    print("\n[2.4] Testing format_news_list - Long summary truncation")
    try:
        test_news = [{
            "id": 1,
            "title": "Test",
            "summary": "A" * 200,  # Very long summary
            "createdAt": "2025-12-11T10:00:00.000Z",
            "_links": {
                "project": {"title": "Project"},
                "author": {"title": "User"}
            }
        }]
        result = format_news_list(test_news)
        assert "..." in result  # Should be truncated
        print("✅ PASSED: Long summary truncated correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2.5: format_news_detail
    print("\n[2.5] Testing format_news_detail")
    try:
        test_news = {
            "id": 5,
            "title": "Detailed News Entry",
            "summary": "Short summary here",
            "description": {
                "raw": "# Main Content\n\nThis is the full content"
            },
            "createdAt": "2025-12-11T10:30:45.123Z",
            "_links": {
                "self": {"href": "/api/v3/news/5"},
                "project": {"href": "/api/v3/projects/1", "title": "My Project"},
                "author": {"href": "/api/v3/users/2", "title": "Jane Smith"}
            }
        }
        result = format_news_detail(test_news)
        assert "📰 News Entry #5" in result
        assert "Detailed News Entry" in result
        assert "My Project" in result
        assert "Jane Smith" in result
        assert "2025-12-11" in result
        assert "Main Content" in result
        print("✅ PASSED: Detail formatted correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    print("\n✅ All formatting tests PASSED")
    return True


async def test_tools_with_mocks():
    """Test news tools with mocked API calls."""
    print("\n" + "=" * 70)
    print("Test 3: Tool Functionality (Mocked)")
    print("=" * 70)
    
    from src.tools.news import (
        list_news,
        create_news,
        get_news,
        update_news,
        delete_news,
        CreateNewsInput,
        UpdateNewsInput
    )
    
    # Test 3.1: list_news with mock
    print("\n[3.1] Testing list_news with mock")
    try:
        with patch('src.tools.news.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_news = AsyncMock(return_value={
                "_embedded": {
                    "elements": [
                        {
                            "id": 1,
                            "title": "Test News",
                            "summary": "Summary",
                            "createdAt": "2025-12-11T10:00:00.000Z",
                            "_links": {
                                "project": {"title": "Project"},
                                "author": {"title": "User"}
                            }
                        }
                    ]
                },
                "total": 1
            })
            mock_get_client.return_value = mock_client
            
            result = await list_news(project_id=1, page_size=10)
            assert "📰 News List" in result
            assert "Test News" in result
            print("✅ PASSED: list_news works correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3.2: list_news with no results
    print("\n[3.2] Testing list_news with no results")
    try:
        with patch('src.tools.news.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_news = AsyncMock(return_value={
                "_embedded": {"elements": []},
                "total": 0
            })
            mock_get_client.return_value = mock_client
            
            result = await list_news()
            assert "No news entries found" in result or "✅" in result
            print("✅ PASSED: Empty result handled correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3.3: create_news with mock
    print("\n[3.3] Testing create_news with mock")
    try:
        with patch('src.tools.news.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_news = AsyncMock(return_value={
                "id": 10,
                "title": "New News Entry",
                "summary": "Summary",
                "description": {"raw": "Content"}
            })
            mock_get_client.return_value = mock_client
            
            input_data = CreateNewsInput(
                project_id=1,
                title="New News Entry",
                summary="Summary",
                description="Content"
            )
            result = await create_news(input_data)
            assert "✅" in result
            assert "10" in result
            print("✅ PASSED: create_news works correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3.4: get_news with mock
    print("\n[3.4] Testing get_news with mock")
    try:
        with patch('src.tools.news.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_news_item = AsyncMock(return_value={
                "id": 5,
                "title": "Detailed News",
                "summary": "Summary",
                "description": {"raw": "Content"},
                "createdAt": "2025-12-11T10:00:00.000Z",
                "_links": {
                    "project": {"title": "Project"},
                    "author": {"title": "User"}
                }
            })
            mock_get_client.return_value = mock_client
            
            result = await get_news(news_id=5)
            assert "📰 News Entry #5" in result
            assert "Detailed News" in result
            print("✅ PASSED: get_news works correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3.5: update_news with mock
    print("\n[3.5] Testing update_news with mock")
    try:
        with patch('src.tools.news.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.update_news = AsyncMock(return_value={
                "id": 5,
                "title": "Updated Title",
                "summary": "Updated Summary"
            })
            mock_get_client.return_value = mock_client
            
            input_data = UpdateNewsInput(
                news_id=5,
                title="Updated Title"
            )
            result = await update_news(input_data)
            assert "✅" in result
            assert "5" in result
            print("✅ PASSED: update_news works correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3.6: delete_news with mock
    print("\n[3.6] Testing delete_news with mock")
    try:
        with patch('src.tools.news.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.delete_news = AsyncMock(return_value=True)
            mock_get_client.return_value = mock_client
            
            result = await delete_news(news_id=5)
            assert "✅" in result
            assert "5" in result
            assert "deleted" in result.lower()
            print("✅ PASSED: delete_news works correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3.7: Error handling
    print("\n[3.7] Testing error handling")
    try:
        with patch('src.tools.news.get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_news = AsyncMock(side_effect=Exception("API Error"))
            mock_get_client.return_value = mock_client
            
            result = await list_news()
            assert "❌" in result
            assert "Failed" in result or "Error" in result
            print("✅ PASSED: Error handled correctly")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    print("\n✅ All tool functionality tests PASSED")
    return True


def run_all_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("NEWS TOOLS - UNIT TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test 1: Pydantic Models
    results.append(("Pydantic Validation", test_pydantic_models()))
    
    # Test 2: Formatting Functions
    results.append(("Formatting Functions", test_formatting_functions()))
    
    # Test 3: Tool Functionality (async)
    results.append(("Tool Functionality", asyncio.run(test_tools_with_mocks())))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("\n" + "=" * 70)
    print(f"Total: {passed}/{total} test suites passed")
    print("=" * 70)
    
    return all(success for _, success in results)


if __name__ == "__main__":
    print("\n>> Starting News Tools Unit Tests...\n")
    success = run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! News tools are ready for integration.\n")
        sys.exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED! Please review the errors above.\n")
        sys.exit(1)
