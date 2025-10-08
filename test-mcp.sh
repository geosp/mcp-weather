#!/bin/bash
# test-mcp.sh - Run test client with uv managed environment

# Exit on error
set -e

# Check if token is provided as parameter
if [ -z "$1" ]; then
    echo "❌ Error: No authentication token provided"
    echo "Usage: ./test-mcp.sh YOUR_AUTHENTIK_TOKEN [LOCATION]"
    echo "Example: ./test-mcp.sh YOUR_TOKEN \"Vancouver, Canada\""
    exit 1
fi

TOKEN="$1"
LOCATION="$2"

# Run the test client with the provided token and optional location
echo "🧪 Running Weather MCP client test..."
if [ -z "$LOCATION" ]; then
    AUTHENTIK_TOKEN="$TOKEN" uv run python tools/test_weather_mcp_client.py
else
    AUTHENTIK_TOKEN="$TOKEN" uv run python tools/test_weather_mcp_client.py "$LOCATION"
fi