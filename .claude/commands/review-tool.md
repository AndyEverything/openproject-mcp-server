# Review MCP Tool Implementation

Review the MCP tool implementation provided in $ARGUMENTS for:

1. **Correctness**
   - Tool definition in `list_tools()` matches implementation in `call_tool()`
   - Input schema validation with Pydantic models
   - Proper async/await patterns
   - Error handling with formatted responses

2. **OpenProject API Integration**
   - Correct endpoint usage
   - Proper authentication flow
   - Response handling and normalization
   - Pagination support where needed

3. **Code Quality**
   - Type hints complete
   - Error messages helpful with hints
   - Response formatting (✅/❌ prefixes)
   - Consistent with existing patterns

4. **Security**
   - Input validation prevents injection
   - No hardcoded credentials
   - Proper error message sanitization

Provide specific, actionable feedback with line numbers.

If no argument provided, ask which tool to review from the available list.
