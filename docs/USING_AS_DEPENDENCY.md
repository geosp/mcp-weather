# Using mcp-weather as a Dependency

This guide shows how to use `mcp-weather` as a dependency in your own MCP server projects to leverage the reusable `core` infrastructure.

## Table of Contents

1. [Installation Methods](#installation-methods)
2. [Quick Start Example](#quick-start-example)
3. [Complete Translation Server Example](#complete-translation-server-example)
4. [What You Get](#what-you-get)
5. [Best Practices](#best-practices)

---

## Installation Methods

### Method 1: Install from Local Directory (Development)

If you have the `mcp-weather` repository locally:

```bash
# In your new project directory
uv add /path/to/mcp-weather

# Or with pip
pip install /path/to/mcp-weather
```

### Method 2: Install from Git Repository

```bash
# Install from GitHub (replace with your actual repo URL)
uv add git+https://github.com/geosp/mcp-weather.git

# Or with pip
pip install git+https://github.com/geosp/mcp-weather.git
```

### Method 3: Install from PyPI (Once Published)

```bash
# After publishing to PyPI
uv add mcp-weather

# Or with pip
pip install mcp-weather
```

### Method 4: Install with Optional Dependencies

```bash
# Install with development tools
uv add "mcp-weather[dev]"

# Install core dependencies only
uv add "mcp-weather[core-only]"
```

---

## Quick Start Example

Here's a minimal example of using the core infrastructure:

### 1. Create Your Project Structure

```bash
mkdir mcp-translation
cd mcp-translation
uv init
```

### 2. Add mcp-weather as Dependency

```bash
# Add the dependency (adjust path as needed)
uv add /path/to/mcp-weather
```

### 3. Create Your Service

```python
# mcp_translation/service.py
from core.server import BaseService
from fastmcp import FastMCP

class TranslationService(BaseService):
    """Simple translation service"""

    def initialize(self) -> None:
        print("Translation service initialized")

    def get_service_name(self) -> str:
        return "translation"

    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def translate(text: str, target_lang: str) -> dict:
            """Translate text to target language"""
            return {
                "original": text,
                "translated": f"[{target_lang}] {text}",  # Mock translation
                "target_language": target_lang
            }
```

### 4. Create Your Server

```python
# mcp_translation/server.py
from typing import List, Optional, Any
from fastapi import FastAPI, APIRouter
from core.server import BaseMCPServer
from core.config import BaseServerConfig
from core.auth_mcp import create_auth_provider

class TranslationServer(BaseMCPServer):
    @property
    def service_title(self) -> str:
        return "Translation MCP Server"

    @property
    def service_description(self) -> str:
        return "Translation service via MCP"

    @property
    def service_version(self) -> str:
        return "1.0.0"

    @property
    def allowed_cors_origins(self) -> List[str]:
        return ["http://localhost:3000"]

    def create_auth_provider(self) -> Optional[Any]:
        return None  # Or: create_auth_provider("translation")

    def create_router(self) -> APIRouter:
        router = APIRouter()

        @router.get("/health")
        async def health():
            return {"status": "healthy"}

        return router

    def register_exception_handlers(self, app: FastAPI) -> None:
        pass

def main():
    from mcp_translation.service import TranslationService

    config = BaseServerConfig.from_env(env_prefix="MCP_")
    service = TranslationService()
    server = TranslationServer(config, service)
    server.run()

if __name__ == "__main__":
    main()
```

### 5. Run Your Server

```bash
# Set environment variables
export MCP_TRANSPORT=http
export MCP_PORT=3000

# Run the server
python -m mcp_translation.server
```

---

## Complete Translation Server Example

See the complete example in [examples/translation-server/](../examples/translation-server/) directory, which includes:

- Full project structure
- Configuration management
- Business logic separation
- Redis caching integration
- Authentik authentication
- REST API endpoints
- Multiple MCP tools
- Error handling
- Logging setup

---

## What You Get

By using `mcp-weather` as a dependency, you get access to:

### Core Infrastructure (`from core import ...`)

```python
# Server base classes
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
```

### Features You Get Automatically

✅ **HTTP & stdio Transport** - Dual transport support
✅ **MCP + REST APIs** - Both interfaces in one server
✅ **Authentication** - Authentik OAuth integration
✅ **Redis Caching** - Async cache client with graceful fallback
✅ **Configuration Management** - Pydantic models + environment variables
✅ **CORS Support** - Configurable origins
✅ **Error Handling** - Exception handlers and logging
✅ **Health Checks** - Built-in endpoints
✅ **Type Safety** - Full type hints throughout

---

## Best Practices

### 1. **Extend, Don't Modify**

Always extend the base classes rather than modifying the core:

```python
# ✅ Good
class MyService(BaseService):
    def initialize(self) -> None:
        # Your initialization
        pass

# ❌ Bad - Don't modify core classes
class BaseService:  # Don't do this!
    def new_method(self):
        pass
```

### 2. **Use Configuration Patterns**

Follow the configuration patterns from `mcp-weather`:

```python
from core.config import BaseServerConfig

class MyServerConfig(BaseServerConfig):
    my_custom_field: str = "default"

    @classmethod
    def from_env(cls) -> "MyServerConfig":
        config = super().from_env(env_prefix="MCP_")
        config.my_custom_field = os.getenv("MY_FIELD", "default")
        return config
```

### 3. **Organize by Features**

Use the feature-based organization pattern:

```
my_mcp_service/
├── features/
│   ├── feature1/
│   │   ├── tool.py      # MCP tool
│   │   ├── routes.py    # REST endpoints
│   │   └── models.py    # Feature models
│   └── feature2/
│       ├── tool.py
│       ├── routes.py
│       └── models.py
```

### 4. **Leverage Caching**

Use the Redis cache client for performance:

```python
from core.cache import RedisCacheClient
from core.config import RedisCacheConfig

config = RedisCacheConfig.from_env(env_prefix="MCP_")
cache = RedisCacheClient(config)

# Store data
await cache.set("my-key", {"data": "value"}, ttl=3600)

# Retrieve data
data = await cache.get("my-key")
```

### 5. **Use Type Hints**

Maintain type safety throughout your code:

```python
from typing import Dict, Any, Optional
from pydantic import BaseModel

class MyRequest(BaseModel):
    field: str
    optional_field: Optional[int] = None

async def my_tool(request: MyRequest) -> Dict[str, Any]:
    return {"result": "value"}
```

### 6. **Environment Variables**

Use consistent naming for environment variables:

```bash
# Server configuration
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=3000
MCP_ONLY=false
MCP_AUTH_ENABLED=true

# Redis configuration
MCP_REDIS_HOST=localhost
MCP_REDIS_PORT=6379
MCP_REDIS_DB=0
MCP_REDIS_NAMESPACE=my-service
MCP_REDIS_TTL=3600

# Authentik configuration (if using auth)
AUTHENTIK_API_URL=http://authentik.example.com
AUTHENTIK_API_TOKEN=your-token-here

# Your service-specific config
MY_SERVICE_API_KEY=your-api-key
MY_SERVICE_API_URL=https://api.example.com
```

### 7. **Docstrings as AI Instructions**

Write comprehensive docstrings for MCP tools - they become instructions for AI:

```python
@mcp.tool()
async def my_tool(param: str) -> dict:
    """
    Brief description of what this tool does

    Detailed explanation that helps AI understand when to use this tool.
    Include examples of user queries this tool can answer.

    Args:
        param: Description of the parameter with examples

    Returns:
        Description of return value structure

    Example Usage:
        User: "How do I do X?"
        AI calls: my_tool("X")
        AI responds: "Here's how to do X..."
    """
    return {"result": "value"}
```

---

## Troubleshooting

### Import Errors

If you get import errors:

```python
# Make sure you're importing from 'core', not 'mcp_weather.core'
from core.server import BaseMCPServer  # ✅ Correct
from mcp_weather.core.server import BaseMCPServer  # ❌ Wrong
```

### Dependency Conflicts

If you have dependency conflicts:

```bash
# Check installed packages
uv pip list

# Reinstall with specific versions
uv add "mcp-weather[core-only]"
```

### Authentication Issues

If authentication isn't working:

1. Ensure `AUTHENTIK_API_URL` and `AUTHENTIK_API_TOKEN` are set
2. Check that `MCP_AUTH_ENABLED=true`
3. Verify Authentik is accessible from your network
4. Check logs for specific error messages

---

## Next Steps

- Review the [complete translation example](../examples/translation-server/)
- Read the [core architecture documentation](../README.md#core-architecture)
- Check out [other example implementations](../examples/)
- Explore the [API reference](../docs/API_REFERENCE.md)

---

## Questions or Issues?

If you encounter problems using `mcp-weather` as a dependency:

1. Check this documentation
2. Review the examples
3. Check the main README.md
4. Open an issue on GitHub
