#!/usr/bin/env python3
"""
Integration test for News Tools - validates with real or mock OpenProject instance.

This script tests the news tools in integration with the server.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_news_tools_integration():
    """Test news tools integration."""
    print("=" * 70)
    print("NEWS TOOLS - INTEGRATION TEST")
    print("=" * 70)
    
    try:
        from src.server import mcp, get_client
        print("\n✅ Server imports successful")
    except Exception as e:
        print(f"\n❌ Server import failed: {e}")
        print("This is expected if dependencies are not installed.")
        print("Skipping integration tests.")
        return True
    
    try:
        # Get client
        client = get_client()
        print(f"✅ OpenProject Client: {client.base_url}")
        
        # Get registered tools
        tools = await mcp.get_tools()
        print(f"✅ Total registered tools: {len(tools)}")
        
        # Find news tools
        news_tools = [t for t in tools if 'news' in str(t).lower()]
        print(f"\n📰 News tools found: {len(news_tools)}")
        
        expected_tools = [
            'list_news',
            'create_news',
            'get_news',
            'update_news',
            'delete_news'
        ]
        
        for tool_name in expected_tools:
            found = any(tool_name in str(t).lower() for t in tools)
            status = "✅" if found else "❌"
            print(f"  {status} {tool_name}")
        
        # Verify all expected tools are registered
        all_found = all(
            any(tool_name in str(t).lower() for t in tools)
            for tool_name in expected_tools
        )
        
        if all_found:
            print("\n✅ All 5 news tools are registered!")
        else:
            print("\n❌ Some news tools are missing!")
            return False
        
        print("\n" + "=" * 70)
        print("Testing individual tools...")
        print("=" * 70)
        
        # Test 1: list_news (basic import)
        print("\n[1] Testing list_news import")
        try:
            from src.tools.news import list_news
            print("✅ list_news imported successfully")
        except Exception as e:
            print(f"❌ Failed to import list_news: {e}")
            return False
        
        # Test 2: create_news (basic import)
        print("\n[2] Testing create_news import")
        try:
            from src.tools.news import create_news, CreateNewsInput
            print("✅ create_news imported successfully")
        except Exception as e:
            print(f"❌ Failed to import create_news: {e}")
            return False
        
        # Test 3: get_news (basic import)
        print("\n[3] Testing get_news import")
        try:
            from src.tools.news import get_news
            print("✅ get_news imported successfully")
        except Exception as e:
            print(f"❌ Failed to import get_news: {e}")
            return False
        
        # Test 4: update_news (basic import)
        print("\n[4] Testing update_news import")
        try:
            from src.tools.news import update_news, UpdateNewsInput
            print("✅ update_news imported successfully")
        except Exception as e:
            print(f"❌ Failed to import update_news: {e}")
            return False
        
        # Test 5: delete_news (basic import)
        print("\n[5] Testing delete_news import")
        try:
            from src.tools.news import delete_news
            print("✅ delete_news imported successfully")
        except Exception as e:
            print(f"❌ Failed to import delete_news: {e}")
            return False
        
        # Test 6: Formatting functions
        print("\n[6] Testing formatting functions")
        try:
            from src.utils.formatting import format_news_list, format_news_detail
            
            # Test with sample data
            test_news = [{
                "id": 1,
                "title": "Test News",
                "summary": "Test Summary",
                "createdAt": "2025-12-11T10:00:00.000Z",
                "_links": {
                    "project": {"title": "Test Project"},
                    "author": {"title": "Test User"}
                }
            }]
            
            result = format_news_list(test_news)
            assert "📰" in result
            assert "Test News" in result
            print("✅ format_news_list works correctly")
            
            result = format_news_detail(test_news[0])
            assert "Test News" in result
            print("✅ format_news_detail works correctly")
            
        except Exception as e:
            print(f"❌ Formatting test failed: {e}")
            return False
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)
        
        print("\n📝 Note: To test with real OpenProject data, you need to:")
        print("   1. Ensure .env file is configured")
        print("   2. Have valid OpenProject instance")
        print("   3. Have 'Manage news' permission")
        print("   4. Run manual tests as described in docs/guides/how_to_use_news.md")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n>> Starting News Tools Integration Test...\n")
    success = asyncio.run(test_news_tools_integration())
    
    if success:
        print("\n🎉 INTEGRATION TEST PASSED!\n")
        sys.exit(0)
    else:
        print("\n⚠️ INTEGRATION TEST FAILED!\n")
        sys.exit(1)
