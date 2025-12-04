# Generate Test Coverage Report

Analyze test coverage for: $ARGUMENTS (default: all tools)

Steps:
1. Run pytest with coverage: `pytest --cov=. --cov-report=term-missing tests/`
2. Identify untested code paths
3. Report coverage statistics by module
4. Suggest priority tests to write

If coverage is below 80%, generate test cases for the most critical untested paths:
- Error handling in tool implementations
- Edge cases in parameter validation
- HTTP error scenarios
- Response formatting

Output format:
- Coverage percentage by file
- List of untested lines
- Priority test recommendations
- Sample test code for critical gaps
