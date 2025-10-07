#!/bin/bash
# test-rest-api.sh - Test the REST API endpoints of Weather MCP Server
# This script is a wrapper around the Python test script

# Exit on error
set -e

# Check if token is provided as parameter
if [ -z "$1" ]; then
    echo "❌ Error: No authentication token provided"
    echo "Usage: ./test-rest-api.sh YOUR_AUTHENTIK_TOKEN"
    exit 1
fi

TOKEN="$1"

echo "🧪 Testing Weather MCP REST API endpoints"
echo "========================================"

# Run the Python test script using uv
uv run python tools/test_rest_api.py "$TOKEN"