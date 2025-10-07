#!/bin/bash
# setup-dev.sh - Set up development environment using uv

# Exit on error
set -e

echo "🔧 Setting up Weather MCP development environment with uv"
echo "========================================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please install uv with:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔨 Creating virtual environment with uv..."
    uv venv .venv
else
    echo "ℹ️ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies with uv
echo "📦 Installing dependencies with uv..."
uv pip install -e .

# Install development dependencies
echo "🧪 Installing development dependencies with uv..."
uv pip install fastmcp 'httpx>=0.24.0' pytest pytest-asyncio

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "   source .venv/bin/activate"
echo ""
echo "To start the Weather MCP server:"
echo "   # Run in MCP-only mode:"
echo "   ./run-server.sh"
echo ""
echo "   # Run in REST API mode (includes MCP endpoints):"
echo "   ./run-server.sh rest"
echo ""
echo "To run the test client, use the run-test.sh script with your token:"
echo "   ./run-test.sh YOUR_AUTHENTIK_TOKEN"