#!/bin/bash
# run-server.sh - Run Weather MCP Server with uv

# Exit on error
set -e

# Default to MCP mode
MODE="mcp"
AUTH="enabled"

# Check for command line arguments
if [ "$1" = "rest" ]; then
  MODE="rest"
fi

if [ "$2" = "noauth" ]; then
  AUTH="disabled"
fi

echo "🚀 Starting Weather MCP Server in $MODE mode..."
echo "🔐 Authentication is $AUTH"

AUTH_FLAG="true"
if [ "$AUTH" = "disabled" ]; then
  AUTH_FLAG="false"
fi

if [ "$MODE" = "mcp" ]; then
  echo "🔧 Running in MCP-only mode (HTTP transport)"
  MCP_TRANSPORT=http MCP_ONLY=true MCP_AUTH_ENABLED=$AUTH_FLAG uv run mcp-weather
else
  echo "🔧 Running in REST API mode (includes MCP endpoints)"
  MCP_TRANSPORT=http MCP_ONLY=false MCP_AUTH_ENABLED=$AUTH_FLAG uv run mcp-weather
fi

# Note: The script will block here until the server is stopped with Ctrl+C