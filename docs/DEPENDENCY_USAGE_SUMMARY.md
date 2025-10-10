# Using mcp-weather as a Dependency - Summary

## What We've Set Up

Your `mcp-weather` project is now configured as a **reusable package** that can be installed with `uv` or `pip` in other projects.

## Files Modified/Created

### Enhanced Configuration
- ✅ **[pyproject.toml](../pyproject.toml)** - Enhanced with proper metadata for distribution
  - Added version constraints for dependencies
  - Added optional dependencies (`dev`, `core-only`)
  - Configured to export both `core` and `mcp_weather` packages
  - Added project metadata (authors, keywords, classifiers, URLs)

### Documentation
- ✅ **[docs/USING_AS_DEPENDENCY.md](USING_AS_DEPENDENCY.md)** - Complete guide
- ✅ **[docs/QUICKSTART_AS_DEPENDENCY.md](QUICKSTART_AS_DEPENDENCY.md)** - 5-minute quick start
- ✅ **[docs/DEPENDENCY_USAGE_SUMMARY.md](DEPENDENCY_USAGE_SUMMARY.md)** - This file

### Complete Example Project
- ✅ **[examples/translation-server/](../examples/translation-server/)** - Full working example
  - `pyproject.toml` - Shows how to depend on mcp-weather
  - `mcp_translation/config.py` - Configuration extension
  - `mcp_translation/translation_service.py` - Business logic
  - `mcp_translation/service.py` - MCP service wrapper
  - `mcp_translation/server.py` - Server implementation
  - `.env.example` - Environment configuration template
  - `README.md` - Complete documentation

## How to Use It

### 1. Install mcp-weather in Your New Project

```bash
# From local directory (development)
cd my-new-mcp-server
uv add /path/to/mcp-weather

# From git repository
uv add git+https://github.com/geosp/mcp-weather.git

# From PyPI (once published)
uv add mcp-weather
```

### 2. Import Core Infrastructure

```python
# Server base classes
from core.server import BaseService, BaseMCPServer

# Caching
from core.cache import RedisCacheClient

# Configuration
from core.config import (
    BaseServerConfig,
    RedisCacheConfig,
    AuthentikConfig
)

# Authentication
from core.auth_mcp import create_auth_provider
from core.auth_rest import verify_token
```

### 3. Extend Base Classes

```python
from core.server import BaseService, BaseMCPServer

class MyService(BaseService):
    def initialize(self) -> None:
        pass

    def get_service_name(self) -> str:
        return "my-service"

    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def my_tool(param: str) -> dict:
            return {"result": param}

class MyServer(BaseMCPServer):
    # Implement required abstract methods
    ...
```

## What You Get for Free

By using `mcp-weather` as a dependency:

✅ **Server Infrastructure**
- HTTP and stdio transport support
- MCP protocol implementation
- FastAPI REST API integration
- Dual interface (MCP + REST)

✅ **Authentication**
- Authentik OAuth integration
- Token validation
- User info extraction
- Flexible auth provider

✅ **Caching**
- Redis-based async caching
- JSON serialization
- Graceful fallback
- Configurable TTL

✅ **Configuration**
- Pydantic models
- Environment variable loading
- Type safety
- Validation

✅ **Error Handling**
- Exception handlers
- HTTP status codes
- Logging integration
- Graceful degradation

✅ **Developer Experience**
- Type hints throughout
- Comprehensive docstrings
- Example implementations
- Documentation

## Project Structure Pattern

When using mcp-weather as a dependency:

```
my-mcp-server/
├── pyproject.toml           # Dependencies (includes mcp-weather)
├── .env                      # Environment variables
├── my_service/
│   ├── __init__.py
│   ├── config.py            # Extend core.config classes
│   ├── business_service.py  # Your business logic
│   ├── service.py           # Extend BaseService
│   └── server.py            # Extend BaseMCPServer
└── README.md

# You do NOT copy the core/ directory!
# It comes from the mcp-weather package
```

## Environment Variables Pattern

Standard environment variables work across all projects using the core:

```bash
# Server configuration
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=3000
MCP_ONLY=false
MCP_AUTH_ENABLED=true
MCP_CORS_ORIGINS=http://localhost:3000

# Redis configuration
MCP_REDIS_HOST=localhost
MCP_REDIS_PORT=6379
MCP_REDIS_DB=0
MCP_REDIS_PASSWORD=
MCP_REDIS_NAMESPACE=my-service
MCP_REDIS_TTL=3600

# Authentik configuration (if auth enabled)
AUTHENTIK_API_URL=http://authentik.example.com
AUTHENTIK_API_TOKEN=your-token

# Your service-specific config
MY_SERVICE_API_KEY=...
MY_SERVICE_API_URL=...
```

## Examples and Templates

### Minimal Example (Quick Start)

See: [docs/QUICKSTART_AS_DEPENDENCY.md](QUICKSTART_AS_DEPENDENCY.md)

Takes 5 minutes to get a working MCP server with:
- HTTP server
- MCP protocol
- REST API
- Basic tool

### Complete Example (Production-Ready)

See: [examples/translation-server/](../examples/translation-server/)

Full implementation with:
- Multiple MCP tools
- REST endpoints
- Business logic separation
- Configuration management
- Redis caching
- Authentication
- Error handling
- Documentation

## Testing Your Setup

### 1. Verify Installation

```bash
# Check mcp-weather is installed
uv pip list | grep mcp-weather

# Should show:
# mcp-weather  0.1.0
```

### 2. Test Imports

```python
# Test core imports work
from core.server import BaseMCPServer
from core.cache import RedisCacheClient
from core.config import BaseServerConfig

print("✅ All imports successful!")
```

### 3. Run Example Project

```bash
cd examples/translation-server

# Install dependencies
uv add ../../

# Configure
cp .env.example .env

# Run
python -m mcp_translation.server
```

## Publishing Your mcp-weather Package

If you want to publish to PyPI for easier installation:

```bash
# Build package
cd /path/to/mcp-weather
python -m build

# Upload to PyPI
python -m twine upload dist/*

# Then users can install with:
# uv add mcp-weather
# pip install mcp-weather
```

## Updating Author Information

Edit [pyproject.toml](../pyproject.toml):

```toml
[project]
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

[project.urls]
Homepage = "https://github.com/geosp/mcp-weather"
Repository = "https://github.com/geosp/mcp-weather"
```

## Common Use Cases

### Use Case 1: Database Query MCP Server

```python
from core.server import BaseService, BaseMCPServer

class DatabaseMCPService(BaseService):
    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def query_database(sql: str) -> dict:
            """Execute SQL query"""
            # Your database logic
            ...
```

### Use Case 2: File Search MCP Server

```python
class FileSearchService(BaseService):
    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def search_files(query: str) -> dict:
            """Search files by content"""
            # Your search logic
            ...
```

### Use Case 3: Email MCP Server

```python
class EmailService(BaseService):
    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def send_email(to: str, subject: str, body: str) -> dict:
            """Send an email"""
            # Your email logic
            ...
```

## Benefits Summary

| Feature | Without Core | With Core |
|---------|-------------|-----------|
| Server Setup | 500+ lines | 50 lines |
| Auth Integration | Custom implementation | `create_auth_provider()` |
| Caching | Build from scratch | `RedisCacheClient` ready |
| Configuration | Manual env parsing | Pydantic models |
| Type Safety | DIY type hints | Built-in throughout |
| MCP Protocol | Learn spec, implement | `BaseMCPServer` ready |
| REST API | Build manually | Automatic integration |
| Error Handling | Custom handlers | Pre-built handlers |
| Documentation | Write from scratch | Examples provided |

## Troubleshooting

### Problem: Import errors

**Solution**: Import from `core`, not `mcp_weather.core`

```python
# ✅ Correct
from core.server import BaseMCPServer

# ❌ Wrong
from mcp_weather.core.server import BaseMCPServer
```

### Problem: Module not found

**Solution**: Verify installation

```bash
uv pip list | grep mcp-weather
# If missing, reinstall:
uv add /path/to/mcp-weather
```

### Problem: Version conflicts

**Solution**: Use optional dependencies

```bash
# Install only core dependencies
uv add "mcp-weather[core-only]"
```

## Next Steps

1. **Review the quick start**: [QUICKSTART_AS_DEPENDENCY.md](QUICKSTART_AS_DEPENDENCY.md)
2. **Study the example**: [examples/translation-server/](../examples/translation-server/)
3. **Read complete guide**: [USING_AS_DEPENDENCY.md](USING_AS_DEPENDENCY.md)
4. **Build your MCP server!**

## Resources

- **Main README**: [../README.md](../README.md)
- **Core Architecture**: [../README.md#core-architecture](../README.md#core-architecture)
- **FastMCP Docs**: https://github.com/jlowin/fastmcp
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **MCP Specification**: https://modelcontextprotocol.io

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [example project](../examples/translation-server/)
3. Read the [complete documentation](USING_AS_DEPENDENCY.md)
4. Open an issue on GitHub

---

**You're now ready to build MCP servers using mcp-weather as a dependency!** 🚀
