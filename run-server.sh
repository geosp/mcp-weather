#!/bin/bash
# run-server.sh - Run Weather MCP Server with uv

# Exit on error
set -e

# Default to MCP mode
MODE="mcp"

# Check for command line argument
if [ "$1" = "rest" ]; then
  MODE="rest"
fi

echo "🚀 Starting Weather MCP Server in $MODE mode..."

if [ "$MODE" = "mcp" ]; then
  echo "🔧 Running in MCP-only mode (HTTP transport)"
  MCP_TRANSPORT=http MCP_ONLY=true uv run mcp-weather
else
  echo "🔧 Running in REST API mode (includes MCP endpoints)"
  MCP_TRANSPORT=http MCP_ONLY=false uv run mcp-weather
fi

# Note: The script will block here until the server is stopped with Ctrl+C