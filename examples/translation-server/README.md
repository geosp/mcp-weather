# Translation MCP Server Example

This is a **complete example** showing how to use `mcp-weather` as a dependency to build a new MCP server.

It demonstrates:
- ✅ Using `mcp-weather` core infrastructure as a package dependency
- ✅ Extending `BaseMCPServer` and `BaseService` classes
- ✅ Implementing custom MCP tools
- ✅ Adding REST API endpoints
- ✅ Configuration management with Pydantic
- ✅ Redis caching integration
- ✅ Optional Authentik authentication
- ✅ Proper error handling and logging

## Features

The Translation MCP Server provides:

### MCP Tools (for AI assistants)
- `translate_text(text, target_language, source_language)` - Translate text
- `detect_language(text)` - Detect text language
- `get_supported_languages()` - List available languages

### REST API Endpoints
- `GET /health` - Health check
- `GET /info` - Service information
- `POST /translate` - Translation endpoint
- `POST /detect` - Language detection
- `GET /languages` - Supported languages list
- `GET /docs` - OpenAPI documentation (Swagger UI)

## Installation

### Prerequisites
- Python 3.10+
- Redis server (for caching)
- `uv` package manager (or `pip`)

### Step 1: Install Dependencies

```bash
# From this directory (examples/translation-server/)
cd examples/translation-server

# Install mcp-weather from parent directory
uv add ../../

# Or if you have mcp-weather in a different location:
# uv add /path/to/mcp-weather

# Or from git:
# uv add git+https://github.com/geosp/mcp-weather.git
```

### Step 2: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env
```

### Step 3: Start Redis (if not already running)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally (Ubuntu/Debian)
sudo apt install redis-server
sudo systemctl start redis
```

## Usage

### Run in MCP-only Mode (stdio)

```bash
# Set transport to stdio in .env
export MCP_TRANSPORT=stdio
export MCP_ONLY=true

# Run the server
python -m mcp_translation.server
```

### Run in HTTP Mode with REST API

```bash
# Set transport to HTTP in .env
export MCP_TRANSPORT=http
export MCP_ONLY=false
export MCP_PORT=3000

# Run the server
python -m mcp_translation.server
```

The server will start at `http://localhost:3000` with:
- MCP endpoint: `http://localhost:3000/mcp`
- REST API: `http://localhost:3000/*`
- API docs: `http://localhost:3000/docs`
- Health check: `http://localhost:3000/health`

### Test the MCP Tools

You can test the MCP tools by connecting GitHub Copilot or using a test client:

```json
// .vscode/mcp.json
{
  "servers": {
    "translation": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Then ask Copilot:
- "Translate 'Hello world' to Spanish"
- "What language is 'Bonjour le monde'?"
- "What languages can you translate?"

### Test the REST API

```bash
# Health check
curl http://localhost:3000/health

# Get service info
curl http://localhost:3000/info

# Translate text
curl -X POST "http://localhost:3000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "target_language": "es",
    "source_language": "auto"
  }'

# Detect language
curl -X POST "http://localhost:3000/detect" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour le monde"}'

# Get supported languages
curl http://localhost:3000/languages
```

## Project Structure

```
mcp_translation/
├── __init__.py              # Package metadata
├── config.py                # Configuration management
├── translation_service.py   # Business logic (API client)
├── service.py               # MCP service wrapper (with feature discovery)
├── server.py                # Server implementation
├── features/                # Feature modules (MODULAR PATTERN)
│   ├── __init__.py
│   ├── translate/           # Translation feature
│   │   ├── __init__.py
│   │   ├── models.py        # Feature-specific models
│   │   ├── tool.py          # MCP tool definition
│   │   └── routes.py        # REST API endpoints
│   ├── detect_language/     # Language detection feature
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── tool.py
│   │   └── routes.py
│   └── supported_languages/ # Supported languages feature
│       ├── __init__.py
│       ├── models.py
│       ├── tool.py
│       └── routes.py
└── shared/                  # Shared models and utilities
    ├── __init__.py
    └── models.py            # Base models, error types
```

**Note**: This follows the **same features pattern** as `mcp-weather`! Each feature is self-contained with:
- `models.py` - Feature-specific Pydantic models
- `tool.py` - MCP tool with `register_tool()` function
- `routes.py` - REST endpoints with `create_router()` function

## How It Works

### Features Pattern (Automatic Discovery)

This example uses **automatic feature discovery** - just like `mcp-weather`!

**Add a new feature in 3 steps:**

1. **Create feature directory**: `features/my_feature/`
2. **Add tool.py**: With `register_tool(mcp, service)` function
3. **Add routes.py** (optional): With `create_router(service)` function

**That's it!** The service automatically:
- Discovers your feature
- Registers MCP tools from `tool.py`
- Includes REST routes from `routes.py`

No manual registration needed! See [service.py](mcp_translation/service.py) and [server.py](mcp_translation/server.py) for the discovery implementation.

### 1. Configuration Layer ([config.py](mcp_translation/config.py))

Extends core configuration classes with service-specific settings:

```python
from core.config import BaseServerConfig

class TranslationAPIConfig(BaseModel):
    api_key: str
    supported_languages: List[str]

class AppConfig(BaseModel):
    server: ServerConfig
    redis_cache: RedisCacheConfig
    translation_api: TranslationAPIConfig
```

### 2. Business Logic Layer ([translation_service.py](mcp_translation/translation_service.py))

Pure business logic, independent of MCP/REST:

```python
class TranslationService:
    async def translate(self, text: str, target_lang: str) -> dict:
        # Translation logic here
        ...
```

### 3. MCP Service Wrapper ([service.py](mcp_translation/service.py))

Implements `BaseService` to expose business logic via MCP:

```python
from core.server import BaseService

class TranslationMCPService(BaseService):
    def register_mcp_tools(self, mcp: FastMCP) -> None:
        @mcp.tool()
        async def translate_text(text: str, target_language: str):
            return await self.translation_service.translate(text, target_language)
```

### 4. Server Implementation ([server.py](mcp_translation/server.py))

Extends `BaseMCPServer` to create the complete server:

```python
from core.server import BaseMCPServer

class TranslationMCPServer(BaseMCPServer):
    @property
    def service_title(self) -> str:
        return "Translation MCP Server"

    def create_router(self) -> APIRouter:
        # Add REST endpoints
        ...
```

## Key Benefits of Using mcp-weather Core

By using `mcp-weather` as a dependency, you get:

✅ **No boilerplate** - Server infrastructure is ready to use
✅ **Dual interfaces** - MCP + REST API automatically
✅ **Authentication** - Authentik OAuth integration built-in
✅ **Caching** - Redis support with graceful fallback
✅ **Configuration** - Environment variable management
✅ **Error handling** - Comprehensive exception handling
✅ **Type safety** - Full Pydantic models and type hints
✅ **Async support** - Async-first design throughout
✅ **Logging** - Structured logging built-in
✅ **CORS** - Configurable CORS support
✅ **Health checks** - Standard endpoints

## Customization

### Add New MCP Tools

Edit [mcp_translation/service.py](mcp_translation/service.py):

```python
def register_mcp_tools(self, mcp: FastMCP) -> None:
    @mcp.tool()
    async def my_new_tool(param: str) -> dict:
        """Tool description for AI"""
        return {"result": "value"}
```

### Add New REST Endpoints

Edit [mcp_translation/server.py](mcp_translation/server.py):

```python
def create_router(self) -> APIRouter:
    router = APIRouter()

    @router.get("/my-endpoint")
    async def my_endpoint():
        return {"data": "value"}

    return router
```

### Add New Configuration

Edit [mcp_translation/config.py](mcp_translation/config.py):

```python
class TranslationAPIConfig(BaseModel):
    my_new_field: str = Field(default="value")
```

## Troubleshooting

### Import Errors

Make sure you're importing from `core`, not `mcp_weather.core`:

```python
from core.server import BaseMCPServer  # ✅ Correct
from mcp_weather.core.server import BaseMCPServer  # ❌ Wrong
```

### Redis Connection Failed

Check Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

If Redis is not available, the server will still work but without caching.

### Module Not Found

Make sure mcp-weather is installed:
```bash
uv pip list | grep mcp-weather
```

If not installed, install it:
```bash
uv add ../../  # From examples/translation-server/
```

## Next Steps

- Add real translation API integration (Google Translate, DeepL, etc.)
- Add more languages
- Implement translation history
- Add batch translation
- Add language pair validation
- Implement rate limiting
- Add metrics and monitoring

## Learn More

- [Using mcp-weather as Dependency](../../docs/USING_AS_DEPENDENCY.md)
- [Main mcp-weather README](../../README.md)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## License

This example is provided as-is for educational purposes.
