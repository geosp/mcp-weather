# Weather MCP Server - Project Structure

## Complete File Organization

```
mcp_weather/
├── __init__.py              # Package exports and metadata
├── config.py                # Configuration management (Pydantic models)
├── cache.py                 # Location caching system (JSON file storage)
├── models.py                # Pydantic request/response models
├── auth_provider.py         # FastMCP auth adapter (uses core.auth)
├── weather_service.py       # Weather API client (Open-Meteo)
├── routes.py                # FastAPI HTTP routes
├── tools.py                 # MCP tool definitions
├── server.py                # Main entry point and app factory
└── README.md                # Documentation (you'll create this)
```

## Module Dependencies

```
server.py
├── config.py (configuration loading)
├── cache.py (via weather_service)
├── weather_service.py (business logic)
├── auth_provider.py (MCP authentication)
│   └── core.auth (your existing infrastructure)
├── routes.py (REST endpoints)
│   ├── weather_service.py
│   ├── models.py
│   └── core.auth
└── tools.py (MCP tools)
    ├── weather_service.py
    └── models.py
```

## Separation of Concerns

### 1. **config.py** - Configuration Layer
- Loads environment variables
- Validates configuration
- Provides typed config objects
- No business logic

### 2. **cache.py** - Data Persistence
- Location coordinate caching
- JSON file operations
- Expiry management
- Independent of weather logic

### 3. **models.py** - Data Models
- Request/response schemas
- Pydantic validation
- OpenAPI documentation
- No business logic

### 4. **auth_provider.py** - Authentication
- Adapts core.auth for FastMCP
- No duplication of auth logic
- Wraps existing AuthentikClient
- Re-exports FastAPI dependencies

### 5. **weather_service.py** - Business Logic
- Weather API client
- Geocoding
- Data transformation
- WMO code translation
- No HTTP/routing concerns

### 6. **routes.py** - HTTP Layer
- FastAPI route definitions
- Request validation
- Error handling
- Uses core.auth for authentication
- Calls weather_service

### 7. **tools.py** - MCP Protocol
- MCP tool definitions
- Tool documentation
- Calls weather_service
- Uses auth_provider

### 8. **server.py** - Application Orchestration
- Application factory
- Configuration validation
- Server startup
- Mode selection (stdio/HTTP/REST+MCP)

## Key Design Patterns

### Dependency Injection
```python
# Weather service injected into routes and tools
weather_service = create_weather_service(config)
router = create_router(weather_service)
register_tools(mcp, weather_service)
```

### Factory Pattern
```python
# Create configured instances
def create_weather_service(config: AppConfig) -> WeatherService:
    cache = LocationCache(config.cache)
    return WeatherService(config.weather_api, cache)
```

### Adapter Pattern
```python
# Adapt existing auth for FastMCP
class AuthentikAuthProvider(AuthProvider):
    def __init__(self):
        self.client = get_authentik_client()  # Use existing
```

### Singleton Pattern
```python
# Global config instance
_config: Optional[AppConfig] = None

def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config
```

## Usage Examples

### 1. Run as MCP-only (stdio)
```bash
python -m mcp_weather.server
```

### 2. Run as MCP-only (HTTP with auth)
```bash
export MCP_TRANSPORT=http
export MCP_ONLY=true
export AUTHENTIK_API_URL=http://authentik.example.com/api/v3
export AUTHENTIK_API_TOKEN=your_token
python -m mcp_weather.server
```

### 3. Run as REST + MCP
```bash
export MCP_TRANSPORT=http
export MCP_ONLY=false
export AUTHENTIK_API_URL=http://authentik.example.com/api/v3
export AUTHENTIK_API_TOKEN=your_token
python -m mcp_weather.server
```

### 4. Use programmatically
```python
from mcp_weather import create_app

app = create_app()

# Run with uvicorn
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=3000)
```

### 5. Use as ASGI app
```bash
gunicorn mcp_weather.server:create_app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:3000
```

## Testing Each Module

### Test config.py
```python
from mcp_weather.config import load_config

config = load_config(validate=False)
print(config.server.transport)
print(config.cache.cache_dir)
```

### Test cache.py
```python
from mcp_weather.cache import LocationCache, LocationData
from mcp_weather.config import CacheConfig

cache = LocationCache(CacheConfig())
data = LocationData(30.4383, -84.2807, "Tallahassee", "US")
cache.set("tallahassee", data)
result = cache.get("tallahassee")
print(result.name, result.latitude, result.longitude)
```

### Test weather_service.py
```python
import asyncio
from mcp_weather import create_weather_service, get_config

async def test():
    config = get_config()
    service = create_weather_service(config)
    weather = await service.get_weather("Tallahassee")
    print(weather.current_conditions.temperature)

asyncio.run(test())
```

### Test routes.py
```python
from fastapi.testclient import TestClient
from mcp_weather import create_app

client = TestClient(create_app())
response = client.get("/health")
assert response.status_code == 200
print(response.json())
```

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_TRANSPORT` | Transport mode (stdio/http) | `stdio` | No |
| `MCP_HOST` | HTTP bind address | `0.0.0.0` | No |
| `MCP_PORT` | HTTP port | `3000` | No |
| `MCP_ONLY` | Pure MCP mode (true/false) | `false` | No |
| `AUTHENTIK_API_URL` | Authentik API URL | - | Yes (HTTP mode) |
| `AUTHENTIK_API_TOKEN` | Authentik API token | - | Yes (HTTP mode) |
| `CACHE_DIR` | Cache directory path | `~/.cache/weather` | No |
| `CACHE_EXPIRY_DAYS` | Cache expiry (days) | `30` | No |
| `WEATHER_API_URL` | Open-Meteo weather URL | (default) | No |
| `WEATHER_GEOCODING_URL` | Open-Meteo geocoding URL | (default) | No |

## Next Steps

1. **Create README.md** with user documentation
2. **Add tests** (pytest for each module)
3. **Create .env.example** with sample configuration
4. **Add deployment docs** (Docker, Kubernetes)
5. **Create API documentation** (separate from OpenAPI)
6. **Add monitoring/metrics** (if needed)
7. **Performance testing** (load testing with locust)
8. **Security audit** (dependency scanning, code review)

## Benefits of This Structure

✅ **Clear separation** - Each file has one responsibility  
✅ **Easy testing** - Modules can be tested independently  
✅ **Maintainable** - Changes isolated to specific files  
✅ **Reusable** - Components can be imported separately  
✅ **Scalable** - Easy to add new features  
✅ **Independent** - Doesn't depend on your bridge's structure  
✅ **No duplication** - Reuses your core.auth infrastructure  
✅ **Type-safe** - Pydantic models throughout  
✅ **Well-documented** - Comprehensive docstrings  
✅ **Production-ready** - Error handling, logging, validation