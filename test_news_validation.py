#!/usr/bin/env python3
"""
Syntax and Structure Validation Test for News Tools.

This test validates:
1. Python syntax correctness
2. File structure
3. Import statements
4. Function/class definitions
"""

import sys
import os
import py_compile
import ast

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_syntax_validation():
    """Test Python syntax for all news-related files."""
    print("=" * 70)
    print("Test 1: Python Syntax Validation")
    print("=" * 70)
    
    files_to_check = [
        "src/tools/news.py",
        "src/client.py",
        "src/utils/formatting.py"
    ]
    
    all_passed = True
    
    for filepath in files_to_check:
        print(f"\n[Checking] {filepath}")
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"  ✅ Syntax OK")
        except py_compile.PyCompileError as e:
            print(f"  ❌ Syntax Error: {e}")
            all_passed = False
    
    return all_passed


def test_file_structure():
    """Test that required functions and classes exist."""
    print("\n" + "=" * 70)
    print("Test 2: File Structure Validation")
    print("=" * 70)
    
    # Test news.py structure
    print("\n[Checking] src/tools/news.py")
    try:
        with open("src/tools/news.py", "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Find all function and class definitions
        functions = []
        async_functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                async_functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        # Check for required classes
        required_classes = ["CreateNewsInput", "UpdateNewsInput"]
        for cls in required_classes:
            if cls in classes:
                print(f"  ✅ Class {cls} found")
            else:
                print(f"  ❌ Class {cls} missing")
                return False
        
        # Check for required async functions (tools)
        required_functions = ["list_news", "create_news", "get_news", "update_news", "delete_news"]
        for func in required_functions:
            if func in async_functions:
                print(f"  ✅ Async function {func} found")
            else:
                print(f"  ❌ Async function {func} missing")
                return False
        
    except Exception as e:
        print(f"  ❌ Failed to parse: {e}")
        return False
    
    # Test client.py for news methods
    print("\n[Checking] src/client.py - News methods")
    try:
        with open("src/client.py", "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Find all method definitions (both sync and async)
        all_methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                all_methods.append(node.name)
        
        required_methods = ["get_news", "get_news_item", "create_news", "update_news", "delete_news"]
        for method in required_methods:
            if method in all_methods:
                print(f"  ✅ Method {method} found")
            else:
                print(f"  ❌ Method {method} missing")
                return False
        
    except Exception as e:
        print(f"  ❌ Failed to parse: {e}")
        return False
    
    # Test formatting.py for news formatting functions
    print("\n[Checking] src/utils/formatting.py - Formatting functions")
    try:
        with open("src/utils/formatting.py", "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        
        required_functions = ["format_news_list", "format_news_detail"]
        for func in required_functions:
            if func in functions:
                print(f"  ✅ Function {func} found")
            else:
                print(f"  ❌ Function {func} missing")
                return False
        
    except Exception as e:
        print(f"  ❌ Failed to parse: {e}")
        return False
    
    return True


def test_documentation():
    """Test that documentation files exist."""
    print("\n" + "=" * 70)
    print("Test 3: Documentation Validation")
    print("=" * 70)
    
    doc_files = [
        "docs/guides/how_to_use_news.md",
    ]
    
    all_exist = True
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            print(f"  ✅ {doc_file} exists")
        else:
            print(f"  ❌ {doc_file} missing")
            all_exist = False
    
    return all_exist


def test_server_integration():
    """Test that server.py includes news import."""
    print("\n" + "=" * 70)
    print("Test 4: Server Integration Validation")
    print("=" * 70)
    
    try:
        with open("src/server.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for news import
        if "from src.tools import news" in content:
            print("  ✅ News import found in server.py")
        else:
            print("  ❌ News import missing in server.py")
            return False
        
        # Check for updated tool count
        if "49 tool" in content or "49 tools" in content:
            print("  ✅ Tool count updated to 49")
        else:
            print("  ⚠️  Tool count might not be updated (expected: 49)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to check server.py: {e}")
        return False


def test_docstrings():
    """Test that all tools have proper docstrings."""
    print("\n" + "=" * 70)
    print("Test 5: Docstring Validation")
    print("=" * 70)
    
    try:
        with open("src/tools/news.py", "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Find all async functions (tools)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                func_name = node.name
                docstring = ast.get_docstring(node)
                
                if docstring:
                    print(f"  ✅ {func_name} has docstring ({len(docstring)} chars)")
                else:
                    print(f"  ❌ {func_name} missing docstring")
                    return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to check docstrings: {e}")
        return False


def run_all_validation_tests():
    """Run all validation tests."""
    print("=" * 70)
    print("NEWS TOOLS - VALIDATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test 1: Syntax
    results.append(("Syntax Validation", test_syntax_validation()))
    
    # Test 2: File Structure
    results.append(("File Structure", test_file_structure()))
    
    # Test 3: Documentation
    results.append(("Documentation", test_documentation()))
    
    # Test 4: Server Integration
    results.append(("Server Integration", test_server_integration()))
    
    # Test 5: Docstrings
    results.append(("Docstrings", test_docstrings()))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION TEST SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("\n" + "=" * 70)
    print(f"Total: {passed}/{total} validation tests passed")
    print("=" * 70)
    
    return all(success for _, success in results)


if __name__ == "__main__":
    print("\n>> Starting News Tools Validation Tests...\n")
    success = run_all_validation_tests()
    
    if success:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("The news tools implementation is structurally correct.")
        print("\n📝 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run unit tests: python test_news_tools.py")
        print("   3. Run integration test: python test_news_integration.py")
        print("   4. Test with real OpenProject instance\n")
        sys.exit(0)
    else:
        print("\n⚠️ SOME VALIDATION TESTS FAILED!")
        print("Please review the errors above.\n")
        sys.exit(1)
