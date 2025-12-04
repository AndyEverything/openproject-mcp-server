# Add New MCP Tool

Create a new MCP tool for OpenProject API endpoint: $ARGUMENTS

Follow this workflow:

1. **Research the API Endpoint**
   - Check OpenProject API v3 documentation
   - Identify required/optional parameters
   - Understand response structure

2. **Add Tool Definition to `list_tools()`**
   - Use descriptive name and description
   - Define input schema with proper types
   - Document all parameters clearly

3. **Implement in `call_tool()`**
   - Add case in match statement
   - Extract and validate arguments
   - Call appropriate OpenProjectClient method
   - Format response with ✅ prefix

4. **Add Client Method (if needed)**
   - Create async method in OpenProjectClient
   - Use `_request()` for HTTP calls
   - Handle errors with helpful messages
   - Normalize response structure

5. **Follow Existing Patterns**
   - Match error handling style
   - Use consistent response formatting
   - Add type hints
   - Include docstrings

6. **Test the Tool**
   - Verify tool appears in tool list
   - Test successful execution
   - Test error scenarios
   - Check response format

Maintain the single-file architecture. Ask for clarification if endpoint details are unclear.
