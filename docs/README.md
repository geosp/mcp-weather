# Documentation Index

This directory contains documentation for using `mcp-weather` as a reusable dependency in your own MCP server projects.

## 📚 Documentation Files

### Quick Start
- **[QUICKSTART_AS_DEPENDENCY.md](QUICKSTART_AS_DEPENDENCY.md)** - Get started in 5 minutes
  - Installation methods
  - Minimal working example
  - Testing your setup
  - Next steps

### Quick Reference
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Cheat sheet for common patterns
  - Installation commands
  - Core imports
  - Code snippets
  - Common patterns
  - Troubleshooting

### Complete Guide
- **[USING_AS_DEPENDENCY.md](USING_AS_DEPENDENCY.md)** - Comprehensive documentation
  - Installation methods
  - Complete examples
  - What you get
  - Best practices
  - Troubleshooting

### Summary
- **[DEPENDENCY_USAGE_SUMMARY.md](DEPENDENCY_USAGE_SUMMARY.md)** - Overview of the setup
  - What was configured
  - How to use it
  - Project structure
  - Common use cases
  - Resources

## 🚀 Getting Started

### New to mcp-weather?

1. Start with **[QUICKSTART_AS_DEPENDENCY.md](QUICKSTART_AS_DEPENDENCY.md)** (5 min read)
2. Check **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** for code snippets
3. Study the **[Translation Server Example](../examples/translation-server/)**

### Ready to build?

1. Follow the **[Quick Start Guide](QUICKSTART_AS_DEPENDENCY.md)**
2. Use **[Quick Reference](QUICK_REFERENCE.md)** while coding
3. Refer to **[Complete Guide](USING_AS_DEPENDENCY.md)** when needed

## 📁 Example Projects

### Translation Server (Complete Example)
Location: [`examples/translation-server/`](../examples/translation-server/)

A production-ready example showing:
- ✅ Multiple MCP tools
- ✅ REST API endpoints
- ✅ Business logic separation
- ✅ Configuration management
- ✅ Redis caching
- ✅ Authentication
- ✅ Error handling
- ✅ Comprehensive documentation

## 🔑 Key Concepts

### What is mcp-weather?

`mcp-weather` provides:
1. **Weather MCP Server** - A working weather service
2. **Reusable Core** - Infrastructure you can use in other projects

### What is the Core?

The `core/` package contains:
- **Server Base Classes** - `BaseService`, `BaseMCPServer`
- **Authentication** - Authentik OAuth integration
- **Caching** - Redis-based async caching
- **Configuration** - Pydantic models for environment variables
- **Utilities** - Error handling, logging, etc.

### How to Use the Core?

Instead of copying code:
1. Install `mcp-weather` as a dependency
2. Import from `core` package
3. Extend base classes
4. Focus on your business logic

## 📖 Documentation Flow

```
┌─────────────────────────────────────────┐
│  New to using mcp-weather as a package? │
└─────────────────┬───────────────────────┘
                  │
                  v
┌─────────────────────────────────────────┐
│  QUICKSTART_AS_DEPENDENCY.md            │
│  • 5-minute tutorial                    │
│  • Minimal example                      │
│  • Get something running quickly        │
└─────────────────┬───────────────────────┘
                  │
                  v
┌─────────────────────────────────────────┐
│  examples/translation-server/           │
│  • Study complete example               │
│  • See production patterns              │
│  • Learn best practices                 │
└─────────────────┬───────────────────────┘
                  │
                  v
┌─────────────────────────────────────────┐
│  QUICK_REFERENCE.md                     │
│  • Code snippets                        │
│  • Common patterns                      │
│  • Use while coding                     │
└─────────────────┬───────────────────────┘
                  │
                  v
┌─────────────────────────────────────────┐
│  USING_AS_DEPENDENCY.md                 │
│  • Complete documentation               │
│  • Detailed explanations                │
│  • Advanced topics                      │
└─────────────────┬───────────────────────┘
                  │
                  v
┌─────────────────────────────────────────┐
│  DEPENDENCY_USAGE_SUMMARY.md            │
│  • Project overview                     │
│  • What was configured                  │
│  • Resource links                       │
└─────────────────────────────────────────┘
```

## 🎯 Common Tasks

### Task: Create a new MCP server

1. Read: [QUICKSTART_AS_DEPENDENCY.md](QUICKSTART_AS_DEPENDENCY.md)
2. Install: `uv add /path/to/mcp-weather`
3. Create: Extend `BaseService` and `BaseMCPServer`
4. Run: `python -m your_service.server`

### Task: Add an MCP tool

1. Reference: [QUICK_REFERENCE.md#add-mcp-tool](QUICK_REFERENCE.md)
2. Implement: In your `service.py`
3. Test: With GitHub Copilot

### Task: Add authentication

1. Reference: [QUICK_REFERENCE.md#add-authentication](QUICK_REFERENCE.md)
2. Configure: Set Authentik environment variables
3. Implement: Return `create_auth_provider()` in server

### Task: Add caching

1. Reference: [QUICK_REFERENCE.md#add-redis-caching](QUICK_REFERENCE.md)
2. Initialize: `RedisCacheClient`
3. Use: `await cache.set()` and `await cache.get()`

## 🛠️ Tools and Resources

### Core Components

| Component | Import | Purpose |
|-----------|--------|---------|
| BaseService | `from core.server import BaseService` | Service interface |
| BaseMCPServer | `from core.server import BaseMCPServer` | Server base class |
| RedisCacheClient | `from core.cache import RedisCacheClient` | Caching |
| BaseServerConfig | `from core.config import BaseServerConfig` | Configuration |
| create_auth_provider | `from core.auth_mcp import create_auth_provider` | Authentication |

### External Documentation

- **FastMCP**: https://github.com/jlowin/fastmcp
- **FastAPI**: https://fastapi.tiangolo.com
- **Pydantic**: https://docs.pydantic.dev
- **Redis**: https://redis.io/docs
- **MCP Spec**: https://modelcontextprotocol.io

## 🐛 Troubleshooting

### Import Errors

```python
# ✅ Correct
from core.server import BaseMCPServer

# ❌ Wrong
from mcp_weather.core.server import BaseMCPServer
```

See: [QUICK_REFERENCE.md#troubleshooting](QUICK_REFERENCE.md#troubleshooting)

### Installation Issues

```bash
# Check if installed
uv pip list | grep mcp-weather

# Reinstall
uv add /path/to/mcp-weather
```

See: [USING_AS_DEPENDENCY.md#troubleshooting](USING_AS_DEPENDENCY.md#troubleshooting)

## 📞 Getting Help

1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for quick answers
2. Review [USING_AS_DEPENDENCY.md](USING_AS_DEPENDENCY.md) for details
3. Study [translation-server example](../examples/translation-server/)
4. Read [main README](../README.md) for architecture details
5. Open an issue on GitHub

## 🤝 Contributing

Found an issue or have a suggestion? Please:
1. Check existing documentation
2. Review example code
3. Open an issue with details

## 📄 License

See [LICENSE](../LICENSE) file in the project root.

---

**Ready to build your MCP server?** Start with the [Quick Start Guide](QUICKSTART_AS_DEPENDENCY.md)! 🚀
