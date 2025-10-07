#!/bin/bash
# run-test.sh - Run test client with uv managed environment

# Exit on error
set -e

# Check if token is provided as parameter
if [ -z "$1" ]; then
    echo "❌ Error: No authentication token provided"
    echo "Usage: ./run-test.sh YOUR_AUTHENTIK_TOKEN"
    exit 1
fi

# Run the test client with the provided token
echo "🧪 Running Weather MCP client test..."
AUTHENTIK_TOKEN="$1" uv run python tools/test_weather_mcp_client.py