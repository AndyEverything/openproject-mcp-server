# Testing

This project includes comprehensive testing setup with both unit tests and end-to-end tests using Docker Compose.

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency. The hooks include:

- **Black**: Code formatting
- **Flake8**: Linting and style checking
- **Pre-commit hooks**: Various checks for trailing whitespace, file endings, YAML syntax, etc.

### Setup Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all hooks manually
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run black
uv run pre-commit run flake8
```

### Configuration

- **Black**: Configured with 88 character line length (see `.pre-commit-config.yaml`)
- **Flake8**: Configured in `.flake8` file with exclusions for `.venv`, `.git`, etc.

## Test Structure

- **Unit Tests** (`tests/test_unit.py`): Test individual components without external dependencies
- **E2E Tests** (`tests/e2e_test.py`): Test complete functionality against a real OpenProject instance
- **Test Data Setup** (`tests/setup_test_data.py`): Script to set up test data in OpenProject

## Running Tests

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local unit tests)

### Unit Tests

Run unit tests locally:

```bash
# Install dependencies
uv sync --extra dev

# Run unit tests
uv run pytest tests/test_unit.py -v
```

### End-to-End Tests

Run the complete E2E test suite using Docker Compose:

```bash
# Make the test runner executable
chmod +x run-e2e-tests.sh

# Run E2E tests
./run-e2e-tests.sh
```

Or run manually:

```bash
# Start services
docker-compose up -d

# Wait for OpenProject to be ready
timeout 300 bash -c 'until curl -f http://localhost:8080/api/v3; do sleep 10; done'

# Run tests
docker-compose run --rm test-runner

# Cleanup
docker-compose down -v
```

### Individual Test Components

You can also run individual components:

```bash
# Start only OpenProject
docker-compose up -d postgres redis openproject

# Run test data setup
docker-compose run --rm test-runner python tests/setup_test_data.py

# Run specific test
docker-compose run --rm test-runner python tests/e2e_test.py
```

## Test Configuration

### Environment Variables

The E2E tests use these environment variables:

- `OPENPROJECT_URL`: OpenProject instance URL (default: http://localhost:8080)
- `OPENPROJECT_API_KEY`: API key for authentication (auto-generated for tests)
- `MCP_SERVER_URL`: MCP server URL (default: http://localhost:8080)
- `LOG_LEVEL`: Logging level (default: DEBUG)

### Docker Services

The test setup includes:

- **PostgreSQL**: Database for OpenProject
- **Redis**: Caching and background jobs
- **OpenProject**: Full OpenProject instance
- **MCP Server**: The MCP server being tested
- **Test Runner**: Executes the test suite

## Test Coverage

The E2E tests cover:

- ✅ API connection testing
- ✅ Project listing and filtering
- ✅ User management
- ✅ Work package type management
- ✅ Priority and status management
- ✅ Work package creation and listing
- ✅ Meeting creation and management
- ✅ Error handling and edge cases

## Continuous Integration

GitHub Actions automatically runs the E2E test suite on:

- Push to main/develop branches
- Pull requests to main
- Manual workflow dispatch

The CI pipeline:

1. Sets up Python environment
2. Installs dependencies with uv
3. Starts Docker services
4. Runs E2E tests
5. Cleans up resources
6. Uploads test results

## Troubleshooting Tests

### Common Issues

1. **OpenProject not ready**: Increase the timeout in the test script
2. **Port conflicts**: Ensure ports 8080 and 5432 are available
3. **Permission errors**: Check Docker permissions and file ownership
4. **Import errors**: Ensure the MCP server module is properly installed

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
docker-compose run --rm test-runner python tests/e2e_test.py
```

### Manual Testing

You can manually test the MCP server:

```bash
# Start services
docker-compose up -d

# Wait for OpenProject
curl -f http://localhost:8080/api/v3

# Test MCP server
docker-compose exec mcp-server python -c "
import asyncio
from openproject_mcp import OpenProjectMCPServer
async def test():
    server = OpenProjectMCPServer()
    server.client = OpenProjectClient('http://openproject:8080', 'test-api-key')
    result = await server.call_tool('test_connection', {})
    print(result[0].text)
asyncio.run(test())
"
```

## Adding New Tests

### Unit Tests

Add new unit tests to `tests/test_unit.py`:

```python
def test_new_feature():
    """Test new feature"""
    # Test implementation
    assert True
```

### E2E Tests

Add new E2E tests to `tests/e2e_test.py`:

```python
async def test_new_feature(self):
    """Test new feature end-to-end"""
    logger.info("Testing new feature...")

    result = await self.mcp_client.call_tool("new_tool", {})

    assert "content" in result
    assert "expected result" in result["content"][0].text

    logger.info("✅ New feature test passed")
```

Don't forget to add the test to the `run_all_tests()` method.
