# Quick Reference - Using mcp-weather as Dependency

## Installation

```bash
# Local development
uv add /path/to/mcp-weather

# From git
uv add git+https://github.com/geosp/mcp-weather.git

# From PyPI (when published)
uv add mcp-weather
```

## Core Imports

```python
# Server infrastructure
from core.server import BaseService, BaseMCPServer, create_server

# Caching
from core.cache import RedisCacheClient

# Configuration
from core.config import (
    BaseServerConfig,
    BaseCacheConfig,
    RedisCacheConfig,
    AuthentikConfig,
    load_dotenv
)

# Authentication
from core.auth_mcp import (
    AuthentikAuthProvider,
    AuthInfo,
    create_auth_provider,
    get_auth_provider
)
from core.auth_rest import verify_token, get_authentik_client

# Authentik client
from core.authentik_client import AuthentikClient

# 🆕 CLI Mode Support (New!)
from core.server import (
    create_standard_cli_parser,
    apply_cli_args_to_environment, 
    create_main_with_modes
)
```

## Minimal Server (50 lines)

```python
# service.py
from core.server import BaseService
from fastmcp import FastMCP

class MyService(BaseService):
    def initialize(self) -> None:
        pass

    def get_service_name(self) -> str:
        return "my-service"

    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def my_tool(param: str) -> dict:
            """Tool description"""
            return {"result": param}

# server.py
from typing import List, Optional, Any
from fastapi import FastAPI, APIRouter
from core.server import BaseMCPServer
from core.config import BaseServerConfig

class MyServer(BaseMCPServer):
    @property
    def service_title(self) -> str:
        return "My Server"

    @property
    def service_description(self) -> str:
        return "Description"

    @property
    def service_version(self) -> str:
        return "1.0.0"

    @property
    def allowed_cors_origins(self) -> List[str]:
        return ["http://localhost:3000"]

    def create_auth_provider(self) -> Optional[Any]:
        return None

    def create_router(self) -> APIRouter:
        router = APIRouter()
        @router.get("/health")
        async def health():
            return {"status": "healthy"}
        return router

    def register_exception_handlers(self, app: FastAPI) -> None:
        pass

def main():
    config = BaseServerConfig.from_env(env_prefix="MCP_")
    service = MyService()
    server = MyServer(config, service)
    server.run()
```

## 🆕 Easy CLI Mode Support (New!)

```python
# Option 1: Automatic main() with --mode support
from core.server import create_main_with_modes

main = create_main_with_modes(
    MyServer,                    # Server class
    lambda config: MyService(),  # Service factory
    lambda: BaseServerConfig.from_env("MCP_"),  # Config factory
    "my-service",               # Service name
    "My MCP Service"            # Description
)

if __name__ == "__main__":
    main()
```

**Now your service automatically supports:**

```bash
python server.py --help                    # Show help
python server.py                           # stdio mode (default)
python server.py --mode mcp --port 3000    # MCP-only HTTP
python server.py --mode rest --port 3000   # REST + MCP HTTP
python server.py --mode mcp --no-auth      # No authentication
```

```python
# Option 2: Manual CLI parsing
from core.server import create_standard_cli_parser, apply_cli_args_to_environment

def main():
    # Parse CLI arguments
    parser = create_standard_cli_parser("my-service")
    args = parser.parse_args()
    
    # Apply to environment
    apply_cli_args_to_environment(args)
    
    # Continue with normal setup
    config = BaseServerConfig.from_env("MCP_")
    service = MyService()
    server = MyServer(config, service)
    server.run()
```

## Environment Variables

```bash
# Server
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=3000
MCP_ONLY=false
MCP_AUTH_ENABLED=true
MCP_CORS_ORIGINS=http://localhost:3000

# Redis
MCP_REDIS_HOST=localhost
MCP_REDIS_PORT=6379
MCP_REDIS_DB=0
MCP_REDIS_PASSWORD=
MCP_REDIS_NAMESPACE=my-service
MCP_REDIS_TTL=3600

# Authentik (optional)
AUTHENTIK_API_URL=http://authentik.example.com
AUTHENTIK_API_TOKEN=your-token
```

## Common Patterns

### Add Redis Caching

```python
from core.cache import RedisCacheClient
from core.config import RedisCacheConfig

config = RedisCacheConfig.from_env(env_prefix="MCP_")
cache = RedisCacheClient(config)

# Use cache
await cache.set("key", {"data": "value"}, ttl=3600)
data = await cache.get("key")
```

### Add Authentication

```python
from core.auth_mcp import create_auth_provider

class MyServer(BaseMCPServer):
    def create_auth_provider(self) -> Optional[Any]:
        return create_auth_provider("my-service")
```

### Add MCP Tool

```python
def register_mcp_tools(self, mcp: FastMCP) -> None:
    @mcp.tool()
    async def tool_name(param: str) -> dict:
        """
        Tool description for AI assistants

        Args:
            param: Parameter description

        Returns:
            Result description
        """
        return {"result": param}
```

### Add REST Endpoint

```python
def create_router(self) -> APIRouter:
    router = APIRouter()

    @router.get("/my-endpoint")
    async def my_endpoint():
        return {"data": "value"}

    @router.post("/my-post")
    async def my_post(data: dict):
        return {"received": data}

    return router
```

### Extend Configuration

```python
from core.config import BaseServerConfig
from pydantic import BaseModel, Field

class MyConfig(BaseModel):
    api_key: str = Field(description="API key")

    @classmethod
    def from_env(cls) -> "MyConfig":
        return cls(api_key=os.getenv("API_KEY", ""))

class AppConfig(BaseModel):
    server: BaseServerConfig
    my_config: MyConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            server=BaseServerConfig.from_env(env_prefix="MCP_"),
            my_config=MyConfig.from_env()
        )
```

## Run Server

```bash
# HTTP mode with REST API
export MCP_TRANSPORT=http
export MCP_PORT=3000
python -m my_service.server

# MCP-only mode (stdio)
export MCP_TRANSPORT=stdio
export MCP_ONLY=true
python -m my_service.server
```

## Test Server

```bash
# Health check
curl http://localhost:3000/health

# API docs
open http://localhost:3000/docs

# Custom endpoint
curl http://localhost:3000/my-endpoint
```

## Connect GitHub Copilot

`.vscode/mcp.json`:

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

## Project Structure

```
my-mcp-server/
├── pyproject.toml          # Include mcp-weather dependency
├── .env                     # Environment variables
├── my_service/
│   ├── __init__.py
│   ├── config.py           # Extend core configs
│   ├── business_logic.py   # Your logic
│   ├── service.py          # Extend BaseService
│   └── server.py           # Extend BaseMCPServer
└── README.md
```

## Troubleshooting

```python
# ✅ Correct import
from core.server import BaseMCPServer

# ❌ Wrong import
from mcp_weather.core.server import BaseMCPServer
```

```bash
# Check installation
uv pip list | grep mcp-weather

# Reinstall
uv add /path/to/mcp-weather
```

## Resources

- [5-Minute Quick Start](QUICKSTART_AS_DEPENDENCY.md)
- [Complete Guide](USING_AS_DEPENDENCY.md)
- [Example Project](../examples/translation-server/)
- [Main README](../README.md)
