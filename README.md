# Weather MCP Server - Project Structure

## Understanding the Model Context Protocol (MCP)

### What is MCP?

The Model Context Protocol (MCP) is a specification for enabling AI assistants like GitHub Copilot to interact with external tools and services. MCP allows AI models to extend their capabilities beyond their training data by connecting to real-time data sources and services.

Key concepts of MCP:
- **Tools**: Functions that an AI assistant can call to retrieve information or perform actions
- **Standardized Interface**: Consistent patterns for tool registration, invocation, and response handling
- **Dynamic Interaction**: AI models can retrieve and use external data during a conversation
- **Stateful Context**: Tools can maintain state between invocations

### Transport Methods: stdio vs. HTTP

MCP supports two primary transport methods, each with different characteristics:

**stdio (Standard Input/Output):**
- **Direct Process Communication**: The AI assistant launches the MCP server as a subprocess
- **Low Latency**: Communication happens through direct pipes without network overhead
- **Simple Setup**: No network configuration required
- **Local Only**: Limited to running on the same machine as the AI client
- **Development Focus**: Primarily used during development and testing

**HTTP:**
- **Network-Based**: Communication over standard HTTP/HTTPS protocols
- **Remote Access**: MCP servers can run anywhere on the network or internet
- **Security Options**: Supports authentication, TLS, and other HTTP security features
- **Scalability**: Allows for load balancing, clustering, and horizontal scaling
- **Production Ready**: Suitable for production deployments serving multiple clients

### Stateful vs. Stateless Approaches

MCP implementations can take different approaches to managing state:

**Stateless (REST-like):**
- **Request-Response Model**: Each tool invocation is a completely independent transaction
- **No Server-Side Session**: The server doesn't maintain client-specific state between requests
- **Simplicity**: Easier to scale horizontally and reason about
- **Resilience**: Service can restart without losing client context
- **Weather MCP Example**: Our implementation is primarily stateless, with each weather request containing all needed context

**Stateful:**
- **Session-Based**: The server maintains session state for each client
- **Context Preservation**: Information from previous interactions can influence current responses
- **Complex Workflows**: Better supports multi-step operations that build on previous results
- **Memory Usage**: Requires server-side storage for session data
- **Potential Applications**: Tools that need to remember previous queries or maintain user preferences

### How Weather MCP Works

The Weather MCP service exposes weather forecast capabilities to AI assistants through the MCP protocol:

1. **Tool Registration**: The service registers the `get_hourly_weather` tool with metadata and parameter schemas
2. **Authentication**: Requests are authenticated using Authentik (an identity provider)
3. **Tool Invocation**: When GitHub Copilot calls the weather tool, the request is processed by our FastMCP handler
4. **Weather Retrieval**: The service:
   - Parses the location input
   - Checks Redis for cached location coordinates
   - If not cached, geocodes the location using Open-Meteo API
   - Retrieves current weather and forecast from Open-Meteo API
   - Formats the response with human-readable descriptions
5. **Response**: The formatted weather data is returned to GitHub Copilot

Our implementation supports both stdio and HTTP transports, and takes a primarily stateless approach where each request is self-contained. We do use Redis caching for performance optimization, but this is transparent to the client and doesn't affect the protocol's stateless nature.

### Framework Integration: FastMCP and FastAPI

This project leverages two powerful frameworks that work together to provide a robust MCP implementation:

**FastMCP:**
- **Purpose**: Implements the Model Context Protocol specification in Python
- **Role in Our Project**: 
  - Provides the core MCP server infrastructure
  - Handles tool registration and invocation
  - Manages request/response serialization
  - Supports both stdio and HTTP transports
  - Processes authentication
- **Advantages**:
  - Reduces boilerplate code for MCP implementation
  - Ensures protocol compliance
  - Handles complex transport details transparently

**FastAPI:**
- **Purpose**: Modern, high-performance web framework for building APIs
- **Role in Our Project**:
  - Provides the HTTP server when operating in HTTP mode
  - Enables RESTful API endpoints alongside MCP
  - Handles request validation with Pydantic models
  - Manages OpenAPI documentation
  - Supports async operations for better performance
- **Advantages**:
  - Excellent performance characteristics
  - Built-in validation and documentation
  - First-class async/await support
  - Type safety with Python type annotations

These frameworks are integrated in the core server implementation, which follows a layered architecture:

1. **FastAPI** handles HTTP routing and REST API endpoints
2. **FastMCP** processes MCP protocol requests and manages tools
3. Our custom **WeatherService** provides the business logic
4. **RedisCacheClient** manages caching for improved performance

### Integration with GitHub Copilot

When a user asks GitHub Copilot about the weather in a location:

1. Copilot recognizes the intent to retrieve weather information
2. Copilot formulates a properly structured request to the Weather MCP service
3. The service authenticates the request using the provided token
4. Weather data is fetched and returned in a structured format
5. Copilot interprets the structured data and presents it to the user in natural language

This interaction happens seamlessly, giving the impression that Copilot has real-time weather knowledge.

### VS Code Integration with mcp.json

To connect GitHub Copilot in VS Code to this weather service, a configuration file at `.vscode/mcp.json` is used. Here's an example:

```json
{
    "servers": {
        "weather-direct-http": {
            "type": "http",
            "url": "http://agentgateway.example.com/weather-mcp",
            "headers": {
                "Authorization": "Bearer YOUR_AUTHENTIK_TOKEN"
            }
        },
        "weather-direct": {
            "type": "stdio",
            "command": "/path/to/your/venv/bin/python",
            "args": ["-m", "mcp_weather.server"]
        }
    },
    "inputs": []
}
```

This configuration allows:

1. **HTTP Connection (Remote Service)**
   - Connect to a hosted weather MCP service
   - Authenticate using an Authentik token
   - Access the service through an agent gateway

2. **Direct stdio Connection (Local Development)**
   - Launch the Python server directly
   - Communicate via standard input/output
   - Useful for development and debugging

3. **SpecBridge Connection (Optional)**
   - Connect through SpecBridge for schema-based validation
   - Useful for testing against the API specification

# Understanding the MCP Weather Service

## What is MCP?

The Model Context Protocol (MCP) is a specialized protocol that allows AI assistants (like GitHub Copilot) to interact with external services. In this project, MCP enables Copilot to access real-time weather data when users ask weather-related questions.

## Architecture Overview

This project implements a weather service with two key interfaces:
1. **MCP API**: For AI assistant interactions
2. **REST API**: For standard web/application access

### Key Components

1. **Server Layer (server.py)**:
   - Extends `BaseMCPServer` from the core module
   - Provides both HTTP and stdio transports
   - Configures authentication with Authentik
   - Sets up CORS, error handling, and routing

2. **Service Layer (weather_service.py)**:
   - Core business logic for weather functionality
   - Handles geocoding (location to coordinates)
   - Fetches weather data from Open-Meteo API
   - Formats responses for both MCP and REST

3. **Feature Modules (`features/hourly_weather/`)**:
   - Modular organization of functionality
   - Contains separate files for:
     - MCP tool definition (tool.py)
     - REST API routes (`routes.py`)
     - Shared data models (`models.py`)

4. **Caching Layer**:
   - Uses Redis for caching location coordinates
   - Improves performance for frequently requested locations

## How MCP Integration Works

The MCP integration is implemented using the `FastMCP` framework:

1. **Tool Registration**:
   ```python
   @mcp.tool()
   async def get_hourly_weather(location: str) -> Dict[str, Any]:
       # Implementation
   ```

2. **Authentication Provider**:
   - Custom `AuthProvider` implementation validates Authentik tokens
   - Token verification ensures only authorized clients can access the service

3. **Dual Transport Support**:
   - HTTP mode: `mcp.http_app()` provides an ASGI application
   - stdio mode: Direct process communication without HTTP overhead

4. **Tool Metadata**:
   - Rich descriptions and examples help AI assistants understand how to use the tool
   - Parameter documentation ensures proper requests

## REST API Integration

The service also provides a REST API using FastAPI:

1. **Endpoint Registration**:
   ```python
   @router.get("/weather")
   async def get_weather(location: str, token_data: TokenData = Depends(verify_token)):
       # Implementation
   ```

2. **Shared Business Logic**:
   - Both MCP tools and REST endpoints use the same `WeatherService` class
   - Ensures consistent behavior across interfaces

3. **API Documentation**:
   - FastAPI generates OpenAPI documentation at `/docs`
   - Includes request/response schemas and authentication requirements

## Authentication Flow

1. The client (AI assistant or web app) sends a request with an Authentik Bearer token
2. The authentication middleware validates the token with Authentik's introspection endpoint
3. If valid, the request proceeds; otherwise, a 401 Unauthorized response is returned

## How to Use This Service

### As an AI Assistant

1. Configure Copilot to connect to this service via mcp.json
2. Ask weather-related questions like "What's the weather in Paris?"
3. The assistant will call the `get_hourly_weather` tool with the location parameter
4. The service returns structured weather data that the assistant interprets for you

### As a REST API Client

```bash
# Get weather for a specific location
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/weather?location=London
```

## Running the Service

The included scripts make it easy to run the service:

```bash
# Run in MCP-only mode
./run-server.sh

# Run with both REST API and MCP endpoints
./run-server.sh rest
```

This architecture provides a clean, modular, and secure implementation of an MCP service that can be used by AI assistants to retrieve real-time weather data.

## Project Structure and Implementation

### Complete File Organization

```
core/
├── __init__.py              # Package exports
├── config.py                # Base configuration classes 
├── cache.py                 # Redis caching infrastructure
├── auth_mcp.py              # MCP authentication providers
├── auth_rest.py             # REST API authentication
├── authentik_client.py      # Client for Authentik API
└── server.py                # Base server infrastructure

mcp_weather/
├── __init__.py              # Package exports and metadata
├── config.py                # Configuration management (Pydantic models)
├── weather_service.py       # Weather API client (Open-Meteo)
├── routes.py                # Base routes (health check, service info)
├── server.py                # Weather-specific server implementation
├── README.md                # Feature-based architecture documentation
├── features/                # Feature modules
│   ├── __init__.py          # Feature discovery
│   ├── README.md            # Feature architecture docs
│   └── hourly_weather/      # Hourly weather feature
│       ├── __init__.py      # Feature exports
│       ├── models.py        # Feature-specific models
│       ├── routes.py        # Feature REST endpoints
│       └── tool.py          # Feature MCP tools
└── shared/                  # Shared components
    ├── __init__.py          # Package exports
    ├── README.md            # Shared components docs
    └── models.py            # Shared models (base classes, errors)
```

## Module Dependencies

```
core/server.py (base infrastructure)
└── core/config.py (base configuration)

mcp_weather/server.py (weather-specific server)
├── core/server.py (inherits BaseMCPServer)
├── config.py (configuration loading)
├── core/cache.py (Redis caching via weather_service)
├── weather_service.py (business logic)
├── shared/models.py (error models)
├── core/auth_mcp.py (MCP authentication)
│   └── core/authentik_client.py
├── routes.py (base routes)
│   └── shared/models.py
├── features/hourly_weather/routes.py (weather endpoints)
│   ├── weather_service.py
│   ├── shared/models.py (errors)
│   ├── hourly_weather/models.py (feature models)
│   └── core/auth_rest.py
└── features/hourly_weather/tool.py (MCP tool)
    ├── weather_service.py
    └── hourly_weather/models.py
```

## Separation of Concerns

### 1. **config.py** - Configuration Layer
- Loads environment variables
- Validates configuration
- Provides typed config objects
- No business logic

### 2. **core/cache.py** - Data Persistence
- Redis-based location coordinate caching
- JSON serialization/deserialization
- Configurable TTL
- Error handling with graceful fallback
- Async-first API
- Independent of weather logic

### 3. **models.py** - Data Models
- Request/response schemas
- Pydantic validation
- OpenAPI documentation
- No business logic

### 4. **core/auth_mcp.py & core/auth_rest.py** - Authentication
- Reusable authentication providers
- Integration with Authentik
- Authentication for both MCP and REST APIs
- Support for token validation

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

### 7. **tools/** - MCP Protocol Tools
- Modular tool implementation
- Automatic discovery and registration
- Tool documentation and metadata
- Each tool in its own file for maintainability

### 8. **core/server.py** - Base Server Infrastructure
- Abstract base classes for services and servers
- Common functionality for all server types
- Support for MCP-only and REST+MCP modes
- Reusable across projects

### 9. **mcp_weather/server.py** - Weather-Specific Server
- Weather service implementation
- Extends base server classes
- Configuration specific to weather service
- Entry point for application

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

### Inheritance and Extension
```python
# Extend base server classes
class WeatherMCPServer(BaseMCPServer):
    @property
    def service_title(self) -> str:
        return "Weather MCP Server"
        
    # ... other overridden methods
```

### Plugin Architecture
```python
# Automatic tool discovery and registration
def register_tools(mcp: FastMCP, weather_service: WeatherService) -> None:
    # Dynamically discover and load all tool modules
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        module = importlib.import_module(f"{package_name}.{module_name}")
        if hasattr(module, "register_tool"):
            module.register_tool(mcp, weather_service)
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

### 6. Test MCP functionality
```bash
# Run test client with authentication token
./test-mcp.sh YOUR_AUTHENTIK_TOKEN

# Test with specific location (supports city, country format)
./test-mcp.sh YOUR_AUTHENTIK_TOKEN "Vancouver, Canada"

# Examples with complex locations
./test-mcp.sh YOUR_TOKEN "Tallahassee, FL, USA"
./test-mcp.sh YOUR_TOKEN "Paris, France"
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
import asyncio
from core.cache import RedisCacheClient
from core.config import RedisCacheConfig

async def test():
    cache_config = RedisCacheConfig(
        host="localhost",
        port=6379,
        db=0,
        namespace="weather",
        ttl=28800  # 8 hours in seconds
    )
    cache = RedisCacheClient(cache_config)
    
    # Store location data
    test_data = {"latitude": 30.4383, "longitude": -84.2807, "name": "Tallahassee", "country": "US"}
    await cache.set("tallahassee", test_data)
    
    # Retrieve location data
    result = await cache.get("tallahassee")
    if result:
        print(result["name"], result["latitude"], result["longitude"])
    
    # Clean up
    await cache.delete("tallahassee")

asyncio.run(test())
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
| `MCP_AUTH_ENABLED` | Enable authentication (true/false) | `true` | No |
| `AUTHENTIK_API_URL` | Authentik API URL | - | Yes (HTTP mode with MCP_AUTH_ENABLED=true) |
| `AUTHENTIK_API_TOKEN` | Authentik API token | - | Yes (HTTP mode with MCP_AUTH_ENABLED=true) |
| `MCP_REDIS_HOST` | Redis server host | `localhost` | No |
| `MCP_REDIS_PORT` | Redis server port | `6379` | No |
| `MCP_REDIS_DB` | Redis database number | `0` | No |
| `MCP_REDIS_PASSWORD` | Redis password | `` | No |
| `MCP_REDIS_NAMESPACE` | Redis key namespace | `weather` | No |
| `MCP_REDIS_TTL` | Cache TTL in seconds | `28800` (8 hours) | No |
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

### Implementation Features

- **Location Intelligence**: Smart handling of ambiguous locations (e.g., distinguishing "Paris, France" from "Paris, Texas")
- **Weather Code Translation**: Converting numeric weather codes to human-readable descriptions
- **Error Resilience**: Graceful degradation when services are unavailable
- **Rate Limiting**: Protection against excessive API usage
- **Caching Strategy**: Only coordinates are cached, ensuring weather data is always current
- **Stateless Design**: Each request is self-contained for horizontal scalability

### Benefits of MCP Integration

For developers, MCP provides:
- **Extended AI Capabilities**: Access to real-time data and specialized services
- **Consistent Interface**: Standardized way to expose functionality to AI assistants
- **Reduced Hallucinations**: AI responses based on factual, current data rather than training data
- **Enhanced Development Experience**: More powerful AI assistance with access to external tools

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