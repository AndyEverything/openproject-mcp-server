#!/bin/bash
# E2E Test Runner Script

set -e

echo "🚀 Starting OpenProject MCP Server E2E Tests"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Generate test API key
export OPENPROJECT_API_KEY="test-api-key-$(date +%s)"
echo "🔑 Generated test API key: $OPENPROJECT_API_KEY"

# Create .env file for testing
cat > .env.test << EOF
OPENPROJECT_URL=http://localhost:8080
OPENPROJECT_API_KEY=$OPENPROJECT_API_KEY
LOG_LEVEL=DEBUG
TEST_CONNECTION_ON_STARTUP=true
EOF

echo "📝 Created test environment file"

# Start services
echo "🐳 Starting Docker services..."
docker compose --env-file .env.test up -d

# Wait for OpenProject to be ready
echo "⏳ Waiting for OpenProject to be ready..."
timeout 300 bash -c 'until curl -f http://localhost:8080/ > /dev/null 2>&1; do
    echo "Waiting for OpenProject..."
    sleep 10
done'

echo "✅ OpenProject is ready!"

# Wait a bit more for full initialization
sleep 30

# Run tests
echo "🧪 Running simplified E2E tests..."
docker compose --env-file .env.test run --rm test-runner

# Capture exit code
TEST_EXIT_CODE=$?

# Cleanup
echo "🧹 Cleaning up..."
docker compose --env-file .env.test down -v
rm -f .env.test

# Exit with test result
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "🎉 All tests passed!"
else
    echo "❌ Tests failed with exit code $TEST_EXIT_CODE"
fi

exit $TEST_EXIT_CODE
