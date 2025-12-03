# Optimize Code Performance

Analyze and optimize performance for: $ARGUMENTS

Focus areas:

1. **Async/Await Patterns**
   - Identify blocking I/O that should be async
   - Check for unnecessary `await` calls
   - Optimize concurrent operations

2. **API Call Efficiency**
   - Batch requests where possible
   - Implement caching for frequently accessed data
   - Reduce redundant API calls

3. **Memory Usage**
   - Large response handling
   - Proper resource cleanup
   - Generator patterns for pagination

4. **Error Handling Overhead**
   - Optimize try/except scopes
   - Avoid catching broad exceptions
   - Fast-fail on validation errors

5. **Response Formatting**
   - Efficient string building
   - Avoid unnecessary data transformations
   - Stream large responses

Provide:
- Performance bottlenecks identified
- Optimization recommendations with code examples
- Expected impact (latency, memory, throughput)
- Trade-offs and considerations

Maintain code readability and maintainability.
