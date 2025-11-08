# Installing and Using mcp-weather as a Dependency

This project can be used in two ways:

1. **As a Weather MCP Server** - Run it directly for weather functionality
2. **As a Dependency** - Use the `core` infrastructure in your own MCP projects

## Using as a Dependency (New Feature! 🎉)

The `mcp-weather` project now includes **reusable core infrastructure** that you can use to build your own MCP servers without copying code.

### Quick Start (5 minutes)

```bash
# Create new project
mkdir my-mcp-server
cd my-mcp-server

# Install mcp-weather as a dependency
uv add /path/to/mcp-weather

# Create your service (see docs/QUICKSTART_AS_DEPENDENCY.md)
```

### What You Get

By installing `mcp-weather` as a dependency, you get access to:

- ✅ **Server Infrastructure** - Base classes for MCP servers
- ✅ **CLI Mode Support** - Standard `--mode` flags (stdio, mcp, rest) 🆕
- ✅ **Authentication** - Authentik OAuth integration
- ✅ **Caching** - Redis-based async caching
- ✅ **Configuration** - Pydantic models for environment variables
- ✅ **Error Handling** - Exception handlers and logging
- ✅ **Type Safety** - Full type hints throughout

### Documentation

📖 **Complete documentation available in [`docs/`](docs/):**

- **[Quick Start (5 min)](docs/QUICKSTART_AS_DEPENDENCY.md)** - Get started immediately
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Code snippets and patterns
- **[Complete Guide](docs/USING_AS_DEPENDENCY.md)** - Comprehensive documentation
- **[Summary](docs/DEPENDENCY_USAGE_SUMMARY.md)** - Overview and resources

### Example Project

📁 **See [`examples/translation-server/`](examples/translation-server/)** for a complete, production-ready example.

### Installation Methods

#### From Local Directory

```bash
uv add /path/to/mcp-weather
```

#### From Git Repository

```bash
uv add git+https://github.com/geosp/mcp-weather.git
```

#### From PyPI (once published)

```bash
uv add mcp-weather
```

### Basic Usage

```python
# Import core infrastructure
from core.server import BaseService, BaseMCPServer
from core.cache import RedisCacheClient
from core.config import BaseServerConfig
from core.auth_mcp import create_auth_provider

# Extend base classes for your service
class MyService(BaseService):
    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def my_tool(param: str) -> dict:
            return {"result": param}

class MyServer(BaseMCPServer):
    # Implement required methods
    ...

# 🆕 NEW: Easy CLI with mode support
from core import create_main_with_modes

main = create_main_with_modes(
    MyServer,
    lambda config: MyService(config),
    load_config,
    "my-service"
)

if __name__ == "__main__":
    main()
```

**Now your service supports standard modes:**

```bash
# Stdio mode (default)
python my_server.py

# MCP-only HTTP server
python my_server.py --mode mcp --port 3000

# Full REST + MCP server  
python my_server.py --mode rest --port 3000 --no-auth
```

## Using as a Weather Server

To run the weather MCP server directly:

```bash
# Install dependencies
uv sync

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python -m mcp_weather.server
```

See [README.md](README.md) for full weather server documentation.

## Choose Your Path

- **Building a new MCP server?** → Start with [docs/QUICKSTART_AS_DEPENDENCY.md](docs/QUICKSTART_AS_DEPENDENCY.md)
- **Want weather functionality?** → See [README.md](README.md)
- **Just exploring?** → Check out [examples/translation-server/](examples/translation-server/)

## More Information

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Main README**: [README.md](README.md)

---

**Ready to build MCP servers with ease?** Start here: [Quick Start Guide](docs/QUICKSTART_AS_DEPENDENCY.md) 🚀
