# Quick Start: Using mcp-weather as a Dependency

This quick start guide shows you how to use `mcp-weather` core infrastructure in your own MCP server project in **under 5 minutes**.

## Overview

Instead of copying code, you'll install `mcp-weather` as a package dependency and import just the `core` infrastructure.

## Prerequisites

- Python 3.10+
- `uv` package manager (recommended) or `pip`
- Redis server (for caching)

## Step 1: Install mcp-weather (2 minutes)

### Option A: From Local Directory (Development)

```bash
# Navigate to your new project
mkdir my-mcp-server
cd my-mcp-server

# Initialize with uv
uv init

# Add mcp-weather as a dependency
uv add /path/to/mcp-weather

# Example:
# uv add ~/projects/mcp/mcp-weather
```

### Option B: From Git Repository

```bash
# Add directly from GitHub
uv add git+https://github.com/geosp/mcp-weather.git
```

### Option C: Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install from local directory
pip install /path/to/mcp-weather

# Or from git
pip install git+https://github.com/geosp/mcp-weather.git
```

## Step 2: Create Your Service (1 minute)

Create `my_mcp_server/service.py`:

```python
from core.server import BaseService
from fastmcp import FastMCP

class MyMCPService(BaseService):
    def initialize(self) -> None:
        print("Service initialized!")

    def get_service_name(self) -> str:
        return "my-service"

    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def hello_world(name: str = "World") -> dict:
            """Say hello to someone"""
            return {"greeting": f"Hello, {name}!"}
```

## Step 3: Create Your Server (1 minute)

Create `my_mcp_server/server.py`:

```python
from typing import List, Optional, Any
from fastapi import FastAPI, APIRouter
from core.server import BaseMCPServer
from core.config import BaseServerConfig

class MyMCPServer(BaseMCPServer):
    @property
    def service_title(self) -> str:
        return "My MCP Server"

    @property
    def service_description(self) -> str:
        return "My awesome MCP service"

    @property
    def service_version(self) -> str:
        return "1.0.0"

    @property
    def allowed_cors_origins(self) -> List[str]:
        return ["http://localhost:3000"]

    def create_auth_provider(self) -> Optional[Any]:
        return None  # No auth for now

    def create_router(self) -> APIRouter:
        router = APIRouter()

        @router.get("/health")
        async def health():
            return {"status": "healthy"}

        return router

    def register_exception_handlers(self, app: FastAPI) -> None:
        pass

def main():
    from my_mcp_server.service import MyMCPService

    config = BaseServerConfig.from_env(env_prefix="MCP_")
    service = MyMCPService()
    server = MyMCPServer(config, service)
    server.run()

if __name__ == "__main__":
    main()
```

## Step 4: Run Your Server (30 seconds)

```bash
# Set environment variables
export MCP_TRANSPORT=http
export MCP_PORT=3000
export MCP_ONLY=false

# Run the server
python -m my_mcp_server.server
```

Your server is now running at:
- **REST API**: http://localhost:3000
- **MCP Endpoint**: http://localhost:3000/mcp
- **API Docs**: http://localhost:3000/docs
- **Health Check**: http://localhost:3000/health

## Test It!

### Test the REST API

```bash
curl http://localhost:3000/health
```

### Test with GitHub Copilot

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "my-server": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Ask Copilot: *"Say hello to Alice"*

Copilot will call your `hello_world` tool!

## What You Got

✅ **HTTP Server** - FastAPI with async support
✅ **MCP Protocol** - Full MCP implementation
✅ **REST API** - Standard HTTP endpoints
✅ **Type Safety** - Pydantic models throughout
✅ **Configuration** - Environment variable management
✅ **Error Handling** - Exception handlers built-in
✅ **CORS Support** - Cross-origin requests enabled
✅ **API Documentation** - Auto-generated OpenAPI docs
✅ **Health Checks** - Standard health endpoint
✅ **Logging** - Structured logging ready

## Next Steps

### Add Redis Caching

```python
from core.cache import RedisCacheClient
from core.config import RedisCacheConfig

config = RedisCacheConfig.from_env(env_prefix="MCP_")
cache = RedisCacheClient(config)

# Use cache
await cache.set("key", {"data": "value"})
data = await cache.get("key")
```

### Add Authentication

```python
from core.auth_mcp import create_auth_provider

class MyMCPServer(BaseMCPServer):
    def create_auth_provider(self) -> Optional[Any]:
        return create_auth_provider("my-service")
```

Set environment variables:
```bash
export MCP_AUTH_ENABLED=true
export AUTHENTIK_API_URL=http://authentik.example.com
export AUTHENTIK_API_TOKEN=your-token
```

### Add More Tools

```python
def register_mcp_tools(self, mcp: FastMCP) -> None:
    @mcp.tool()
    async def another_tool(param: str) -> dict:
        """Tool description for AI assistants"""
        return {"result": param}
```

### Add REST Endpoints

```python
def create_router(self) -> APIRouter:
    router = APIRouter()

    @router.post("/my-endpoint")
    async def my_endpoint(data: dict):
        return {"received": data}

    return router
```

## Complete Example

See the full [Translation Server Example](../examples/translation-server/) for a production-ready implementation with:
- Multiple MCP tools
- REST API endpoints
- Redis caching
- Configuration management
- Error handling
- Comprehensive documentation

## Learn More

- [Complete Documentation](USING_AS_DEPENDENCY.md)
- [Translation Server Example](../examples/translation-server/README.md)
- [Main README](../README.md)

## Troubleshooting

**Import errors?**
```python
# Use this:
from core.server import BaseMCPServer

# NOT this:
from mcp_weather.core.server import BaseMCPServer
```

**Module not found?**
```bash
# Check installation
uv pip list | grep mcp-weather

# Reinstall
uv add /path/to/mcp-weather
```

**Need help?** Check the [complete documentation](USING_AS_DEPENDENCY.md) or open an issue.
