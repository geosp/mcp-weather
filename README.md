# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather tools using FastMCP 2.0 framework with both MCP protocol and REST API support.

## Overview

This project provides a comprehensive weather service with multiple deployment options:

1. **Dynamic MCP Deployment** - Pure MCP protocol with K-Gateway integration (RECOMMENDED)
2. **REST API Deployment** - Standard HTTP API with OpenAPI documentation  
3. **Manual Manifests** - Basic kubectl deployment for development

## Features

- ✅ **FastMCP 2.0** - Modern MCP framework with HTTP transport
- ✅ **Pure MCP Mode** - `MCP_ONLY=true` for protocol-only operation
- ✅ **REST API Mode** - `MCP_ONLY=false` for HTTP + FastAPI integration
- ✅ **Open-Meteo Integration** - Free weather data (no API key required)
- ✅ **Kubernetes Ready** - Production deployment with K-Gateway
- ✅ **Dynamic Backend** - Auto-discovery with label selectors
- ✅ **VS Code Integration** - Direct MCP extension support

## Architecture Comparison

### Dynamic MCP (Recommended)
```
GitHub Copilot ←→ VS Code MCP Extension ←→ HTTP ←→ K-Gateway (MCP Backend)
                                                       ↓ /weather-dynamic/*
                                                   Weather Service (MCP)
                                                       ↓ HTTP
                                                   Open-Meteo API
```

### REST API
```
HTTP Client ←→ K-Gateway (Static Backend) ←→ Weather Service (REST)
Browser           ↓ /weather-api/*              ↓ FastAPI + OpenAPI
curl, Postman     ↓                             ↓ HTTP
                  ↓                         Open-Meteo API
```

## Quick Start

### Option 1: Dynamic MCP (For MCP Tools)
```bash
cd examples/kubernetes
ansible-playbook deploy-weather-mcp-dynamic.yml
```

**Then configure VS Code MCP extension** in `.vscode/mcp.json`:
```json
{
  "servers": {
    "weather-dynamic-http": {
      "type": "http",
      "url": "http://agentgateway.mixwarecs-home.net/weather-dynamic/"
    }
  }
}
```

### Option 2: REST API (For HTTP Clients)
```bash
cd examples/kubernetes  
ansible-playbook deploy-weather-rest-api.yml
```

**Test with curl:**
```bash
curl "http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Paris"
curl http://agentgateway.mixwarecs-home.net/weather-api/docs
```

### Option 3: Manual Deployment (Development)
```bash
cd examples/kubernetes/manifests/mcp-dynamic
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-service.yaml
kubectl apply -f 04-gateway.yaml
```

## VS Code MCP Integration

After deploying the Dynamic MCP service, configure VS Code MCP extension in `.vscode/mcp.json`:

### Production Configuration (Recommended)
```json
{
  "servers": {
    "weather-dynamic-http": {
      "type": "http",
      "url": "http://agentgateway.mixwarecs-home.net/weather-dynamic/"
    }
  },
  "inputs": []
}
```

### Complete Configuration Example
This example shows a production setup with local development options:

```json
{
  "servers": {
    // Active: Dynamic MCP deployment (production)
    "weather-dynamic-http": {
      "type": "http", 
      "url": "http://agentgateway.mixwarecs-home.net/weather-dynamic/"
    },
    
    // Local development (uncomment for local testing)
    // MCP_ONLY=true uv run python -m mcp_weather.weather --transport http --port 8000
    // "weather-local": {
    //   "type": "http",
    //   "url": "http://localhost:8000/"
    // },
    
    // Legacy stdio configurations (kept for reference)
    // "weather-direct": {
    //   "type": "stdio", 
    //   "command": "/path/to/python",
    //   "args": ["-m", "mcp_weather.weather"]
    // }
  },
  "inputs": []
}
```

### Testing MCP Integration

After configuring `.vscode/mcp.json`:

1. **Restart VS Code** to load the new MCP configuration
2. **Open GitHub Copilot Chat** 
3. **Test weather queries:**
   ```
   "What's the weather in Tokyo?"
   "Get weather forecast for Madrid" 
   "How's the weather in your location?" (if location detection works)
   ```

### Configuration Tips

- **Use HTTP type** for deployed services (not stdio)
- **URL should end with `/`** for proper routing
- **Match the deployment path** (`/weather-dynamic/` for Dynamic MCP)
- **Keep local options commented** for easy development switching
- **Restart VS Code** after configuration changes

## Project Structure

```
mcp-weather/
├── README.md                                    # This documentation
├── .vscode/
│   └── mcp.json                                # MCP client configuration
├── mcp_weather/                                # Python FastMCP weather service
│   ├── __init__.py
│   └── weather.py                              # Main weather service implementation
├── examples/                                   # Deployment examples
│   ├── README.md                               # Examples overview
│   └── kubernetes/                             # Kubernetes deployment examples
│       ├── deploy-weather-mcp-dynamic.yml      # Dynamic MCP deployment (RECOMMENDED)
│       ├── deploy-weather-rest-api.yml         # REST API deployment
│       ├── cleanup-weather-mcp-dynamic.yml     # Dynamic MCP cleanup
│       ├── cleanup-weather-rest-api.yml        # REST API cleanup
│       └── manifests/                          # Manual kubectl deployment
│           ├── mcp-dynamic/                    # MCP with Dynamic Backend
│           └── rest-api/                       # REST with Static Backend
├── pyproject.toml                              # Python dependencies and build config
├── Dockerfile                                  # Container for deploying weather service
├── .github/workflows/
│   └── docker-publish.yml                     # CI/CD for container deployment
└── uv.lock                                    # Python dependency lock file
```

## Deployment Options

### 1. Dynamic MCP Deployment (RECOMMENDED)
**Best for:** VS Code MCP extension, GitHub Copilot, MCP tools

**Features:**
- ✅ Pure MCP protocol (`MCP_ONLY=true`)
- ✅ Dynamic Backend with label selectors
- ✅ StreamableHTTP transport protocol
- ✅ Shows as "MCP Service" in K-Gateway UI
- ✅ Auto-discovery and scaling

**Usage:**
```bash
cd examples/kubernetes
ansible-playbook deploy-weather-mcp-dynamic.yml
```

**Access:** Configure in `.vscode/mcp.json`:
```json
{
  "servers": {
    "weather-dynamic-http": {
      "type": "http",
      "url": "http://agentgateway.mixwarecs-home.net/weather-dynamic/"
    }
  }
}
```

### 2. REST API Deployment
**Best for:** Web applications, HTTP clients, API documentation

**Features:**
- ✅ REST + FastAPI mode (`MCP_ONLY=false`)
- ✅ Static Backend with explicit routing
- ✅ OpenAPI documentation at `/docs`
- ✅ CORS enabled for browser access
- ✅ Interactive Swagger UI

**Usage:**
```bash
cd examples/kubernetes
ansible-playbook deploy-weather-rest-api.yml
```

**Endpoints:**
- Health: `http://agentgateway.mixwarecs-home.net/weather-api/health`
- Weather: `http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Paris`
- Docs: `http://agentgateway.mixwarecs-home.net/weather-api/docs`

### 3. Manual Manifests
**Best for:** Development, testing, learning

See `examples/kubernetes/manifests/` for kubectl-based deployment.

## Key Technical Concepts

### MCP Protocol Modes

#### MCP_ONLY=true (Pure MCP)
- **Purpose:** Direct MCP protocol for AI tools
- **Transport:** StreamableHTTP for proper K-Gateway recognition
- **Backend:** Dynamic with label selectors
- **Client:** VS Code MCP extension, GitHub Copilot
- **UI Recognition:** Shows as "MCP Service" in K-Gateway

#### MCP_ONLY=false (REST + MCP)
- **Purpose:** HTTP API with FastAPI integration
- **Transport:** Standard HTTP protocol
- **Backend:** Static with explicit host/port
- **Client:** Browsers, curl, HTTP libraries
- **UI Recognition:** Shows as "Static" in K-Gateway

### Backend Types

#### Dynamic Backend (MCP)
```yaml
spec:
  type: MCP
  selector:
    matchLabels:
      app: weather-mcp-dynamic
      component: mcp-server
```
- ✅ Auto-discovery via label selectors
- ✅ Proper MCP type recognition
- ✅ Scales with service replicas
- ✅ Service mesh integration

#### Static Backend (REST)
```yaml
spec:
  type: Static
  static:
    hosts:
      - host: weather-rest-api.ai-services.svc.cluster.local
        port: 80
```
- ✅ Explicit routing configuration
- ✅ Standard HTTP load balancing
- ✅ CORS and traffic policies
- ❌ Manual configuration required

### K-Gateway Integration

Both deployment types integrate with K-Gateway but appear differently:

| Feature | Dynamic MCP | Static REST |
|---------|-------------|-------------|
| **UI Display** | "MCP Service" | "Static" |
| **Discovery** | Automatic | Manual |
| **Protocol** | StreamableHTTP | HTTP |
| **Auth Bypass** | Supported | Supported |
| **Scaling** | Auto | Manual |

## Components

### FastMCP Weather Service
- **Framework:** FastMCP 2.0 with FastAPI integration
- **Transport:** HTTP with configurable MCP modes
- **Data Source:** Open-Meteo API (free, no API key required)
- **Deployment:** Kubernetes with K-Gateway integration
- **Features:** Location-based weather, caching, error handling

### Environment Variables
```bash
# Core configuration
MCP_TRANSPORT=http          # Transport protocol
MCP_HOST=0.0.0.0           # Bind address
MCP_PORT=8000              # Service port

# Mode selection
MCP_ONLY=true              # Pure MCP protocol (recommended for tools)
MCP_ONLY=false             # REST + MCP mode (recommended for HTTP clients)
```

### Deployment Validation

Both deployment options include comprehensive testing:

#### Dynamic MCP Testing
```bash
# Health check via K-Gateway
curl http://agentgateway.mixwarecs-home.net/weather-dynamic/health

# MCP integration test (VS Code)
# Configure .vscode/mcp.json and test in GitHub Copilot:
# "What's the weather in Tokyo?"
```

#### REST API Testing  
```bash
# Health check
curl http://agentgateway.mixwarecs-home.net/weather-api/health

# Weather API
curl "http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Rome"

# OpenAPI documentation
curl http://agentgateway.mixwarecs-home.net/weather-api/openapi.json

# Interactive docs
open http://agentgateway.mixwarecs-home.net/weather-api/docs
```

## Production Considerations

### When to Use Dynamic MCP
- ✅ **MCP tool integration** (VS Code, GitHub Copilot)
- ✅ **Direct protocol support** needed
- ✅ **Service auto-discovery** preferred
- ✅ **K-Gateway MCP recognition** important

### When to Use REST API
- ✅ **Web application integration**
- ✅ **OpenAPI documentation** needed
- ✅ **CORS support** for browsers
- ✅ **Standard HTTP clients**

### Security and Authentication

Both deployments use K-Gateway TrafficPolicy to disable authentication:

```yaml
spec:
  authConfig:
    disabled: true  # Required for tool access
```

**Important:** This is intentional for MCP tool integration. For production, consider:
- Restricting access by IP/network
- Using separate authenticated endpoints for management
- Monitoring usage patterns

### Scaling and High Availability

Both deployments support:
- **2 replicas** by default
- **Health checks** with automatic restart
- **Resource limits** for stability
- **Load balancing** via Kubernetes services

## Cleanup

Each deployment includes cleanup automation:

```bash
# Clean up Dynamic MCP deployment
ansible-playbook cleanup-weather-mcp-dynamic.yml

# Clean up REST API deployment
ansible-playbook cleanup-weather-rest-api.yml
```
    }
  }
}
```
- **Use Case**: Local service deployment, testing HTTP transport
- **Deployment**: Local or simple cloud service
- **Scaling**: Manual service management

**3. Enterprise MCP (Our Approach - Advanced)**
```json
// .mcp.json
{
  "servers": {
    "weather-specbridge": {
      "type": "stdio",
      "command": "/path/to/node",
      "args": ["/path/to/specbridge", "--specs", "/specs/dir"]
    }
  }
}
```
- **Use Case**: Production services, enterprise integration
- **Deployment**: Kubernetes, service mesh, API gateway
- **Scaling**: Full container orchestration

#### Production Readiness Checklist

Based on the Ansible deployment, here's what makes an MCP service production-ready:

**Infrastructure Requirements:**
- ✅ Container deployment with resource limits
- ✅ Multiple replicas for high availability  
- ✅ Health checks (liveness and readiness probes)
- ✅ Service discovery (Kubernetes DNS)
- ✅ Load balancing (ClusterIP + LoadBalancer)

**Gateway Integration:**
- ✅ API gateway routing (K-Gateway HTTPRoute)
- ✅ Authentication policies (Static backend + TrafficPolicy)
- ✅ Service-based URL patterns (`/weather-service/*`)
- ✅ URL rewriting for clean service interfaces

**Monitoring and Operations:**
- ✅ Prometheus metrics endpoints
- ✅ Structured logging
- ✅ Deployment validation testing
- ✅ Cleanup procedures for legacy resources

**MCP Bridge Configuration:**
- ✅ OpenAPI specification exposure
- ✅ Automatic tool generation (Specbridge)
- ✅ stdio transport for client compatibility
- ✅ Error handling and retry logic

### Real-World Usage Patterns

#### Development Workflow
1. **Local Development**: stdio MCP for rapid iteration
2. **Integration Testing**: HTTP MCP on local/staging
3. **Production Deployment**: Enterprise MCP with full infrastructure

#### Multi-Service Architecture
```
MCP Clients (Copilot, Claude, etc.)
    ↓ (stdio)
Specbridge Aggregator
    ↓ (HTTP)
API Gateway (K-Gateway)
    ↓ (Service Routes)
┌─────────────────┬─────────────────┬─────────────────┐
│ Weather Service │ Finance Service │ Document Service│
│ /weather-*      │ /finance-*      │ /document-*     │
└─────────────────┴─────────────────┴─────────────────┘
```

This pattern enables:
- **Service Independence**: Each service deployed separately
- **Unified MCP Interface**: Single Specbridge aggregates all services
- **Gateway Benefits**: Authentication, routing, monitoring per service
- **Client Simplicity**: One MCP configuration accessing all tools

## Setup Instructions

### Prerequisites
- **Node.js** (via nvm recommended) - for Specbridge
- **Python 3.11+** (via uv) - for local weather service development
- **VS Code** with GitHub Copilot - for testing MCP integration

### Quick Start (Using Deployed Service)

1. **Install Specbridge globally:**
   ```bash
   npm install -g specbridge
   ```

2. **Clone and setup project:**
   ```bash
   git clone <repository-url>
   cd mcp-weather
   ```

3. **Download OpenAPI spec from deployed service:**
   ```bash
   curl -s http://agentgateway.mixwarecs-home.net/weather-service/openapi.json > specs/weather-service.json
   ```

4. **Update OpenAPI spec** to include server URL (already done):
   ```json
   {
     "servers": [
       {
         "url": "http://agentgateway.mixwarecs-home.net/weather-service",
         "description": "Weather service deployment"
       }
     ]
   }
   ```

5. **Configure MCP client** (already configured in `.vscode/mcp.json`):
   ```json
   {
     "servers": {
       "weather-specbridge": {
         "type": "stdio",
         "command": "/home/geo/.nvm/versions/node/v24.9.0/bin/node",
         "args": ["/home/geo/.nvm/versions/node/v24.9.0/bin/specbridge", "--specs", "/home/geo/projects/mcp/mcp-weather/specs"]
       }
     },
     "inputs": []
   }
   ```

   **⚠️ Important**: Update the Node.js path to match your nvm installation.

## Deployment Examples

For production deployments, see the **[examples directory](examples/)** which includes:

### Kubernetes Deployment Options

1. **[Ansible Playbook](examples/kubernetes/deploy-weather-mcp.yml)** (Recommended)
   - Full automation with validation and testing
   - K-Gateway integration with authentication bypass
   - Service-based routing pattern (`/weather-service/*`)
   - High availability with health monitoring

2. **[Kubectl Manifests](examples/kubernetes/manifests/)** (Manual)
   - Direct YAML deployment
   - Simpler for learning or GitOps workflows
   - Requires manual customization and testing

**Quick Kubernetes deployment:**
```bash
# Option 1: Ansible (full automation)
cd examples/kubernetes
ansible-playbook deploy-weather-mcp.yml

# Option 2: kubectl (manual)
cd examples/kubernetes/manifests
kubectl apply -f .
```

See **[examples/README.md](examples/README.md)** for detailed deployment guides.

### Local Development (Optional)

If you want to develop the weather service locally:

1. **Install Python dependencies:**
   ```bash
   uv sync
   ```

2. **Run local weather service:**
   ```bash
   uv run mcp-weather
   ```

3. **Update specs/weather-service.json** to point to localhost:3000

## Testing with GitHub Copilot

### Successful Integration Test

This project has been **successfully tested with GitHub Copilot** using the following approach:

1. **MCP Configuration**: The `.vscode/mcp.json` file configures Specbridge as an MCP server
2. **Tool Discovery**: Copilot successfully discovered **14 tools** including weather functions
3. **Weather Queries**: Copilot can respond to weather questions using the MCP tools

### Example Test Results

**Query**: "What's the weather in Paris?"

**Copilot Response**: Successfully retrieved weather data showing:
- Temperature: 17.4°C (feels like 14.7°C)
- Conditions: Partly cloudy
- Humidity: 42%
- Wind: 8.9 km/h from Southeast
- Complete hourly forecast data

### Available MCP Tools

Specbridge automatically generates **14 total tools**:

#### Weather Tools (3)
- `weatherservice_get_weather_http_weather_get` - Get weather data for any location
- `weatherservice_health_health_get` - Check weather service health  
- `weatherservice_root__get` - Get API information

#### Built-in Specbridge Tools (11)
- `specbridge_list_specs` - List OpenAPI specifications
- `specbridge_get_spec` - Get specification content
- `specbridge_update_spec` - Update specification
- `specbridge_download_spec` - Download specs from URLs
- **APIs.guru discovery tools** (7 additional tools for API discovery)

## Usage Examples

### Weather Queries in GitHub Copilot
```
"What's the weather in Paris?"
"Get me the weather forecast for Tokyo"
"Check current weather conditions in London"
"How's the weather in New York?"
```

### Expected Response Format
```json
{
  "location": "Paris",
  "country": "France",
  "coordinates": {"latitude": 48.85341, "longitude": 2.3488},
  "timezone": "Europe/Paris",
  "current_conditions": {
    "temperature": {"value": 17.4, "unit": "°C"},
    "feels_like": {"value": 14.7, "unit": "°C"},
    "humidity": {"value": 42, "unit": "%"},
    "weather": "Partly cloudy",
    "wind": {"speed": 8.9, "direction": "SE", "unit": "km/h"},
    "precipitation": {"value": 0, "unit": "mm"}
  },
  "hourly_forecast": [
    {
      "time": "2025-10-02T18:00",
      "temperature": {"value": 14.8, "unit": "°C"},
      "weather": "Mainly clear",
      "precipitation_probability": {"value": 0, "unit": "%"}
    }
  ],
  "data_source": "Open-Meteo API (https://open-meteo.com)"
}
```

## Troubleshooting

### Common MCP Integration Issues

1. **"node: No such file or directory" (Error 127)**
   - **Cause**: MCP client can't find Node.js in PATH
   - **Solution**: Use full path to node in `mcp.json` configuration
   - **Fixed**: ✅ Current config uses absolute path

2. **"Process exited with code 127"**
   - **Cause**: Incorrect command path in configuration  
   - **Solution**: Verify Node.js and Specbridge paths are correct
   - **Status**: ✅ Resolved with current configuration

3. **Specbridge server not starting**
   - **Cause**: Missing OpenAPI spec or incorrect path
   - **Solution**: Ensure `specs/weather-service.json` exists and paths are correct
   - **Status**: ✅ Working with current setup

4. **MCP tools not discovered**
   - **Cause**: GitHub Copilot Chat MCP support limitations
   - **Solution**: Use compatible MCP client or VS Code extension
   - **Note**: Successfully tested with GitHub Copilot integration

### Verification Commands

Check if Specbridge is running:
```bash
ps aux | grep specbridge | grep -v grep
```

Test Specbridge manually:
```bash
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}' | specbridge --specs /path/to/specs
```

Test deployed weather service:
```bash
curl "http://agentgateway.mixwarecs-home.net/weather-service/weather?location=Paris"
```

## Development

### Local Development
```bash
# Clone repository
git clone https://github.com/geosp/mcp-weather.git
cd mcp-weather

# Install dependencies
uv sync

# Run MCP-only mode (for MCP tools)
MCP_ONLY=true uv run python -m mcp_weather.weather --transport http --port 8000

# Run REST API mode (for HTTP clients)  
MCP_ONLY=false uv run python -m mcp_weather.weather --transport http --port 8000
```

### Container Development
```bash
# Build container
docker build -t mcp-weather .

# Run MCP mode
docker run -p 8000:8000 -e MCP_ONLY=true mcp-weather

# Run REST mode
docker run -p 8000:8000 -e MCP_ONLY=false mcp-weather
```

### Testing Locally
```bash
# Health check
curl http://localhost:8000/health

# Weather API (REST mode only)
curl "http://localhost:8000/weather?location=Paris"

# MCP protocol test (MCP mode only, requires MCP client)
# Configure .vscode/mcp.json with http://localhost:8000/
```

## Troubleshooting

### Common Issues

**1. "Session terminated" errors in MCP mode**
- Ensure `MCP_ONLY=true` is set
- Verify no FastAPI mounting is occurring
- Check VS Code MCP extension configuration

**2. K-Gateway shows "Static" instead of "MCP Service"**
- Verify Backend `type: MCP` is set
- Check label selectors match service labels
- Ensure StreamableHTTP appProtocol is configured

**3. CORS errors in REST API**
- Check TrafficPolicy CORS configuration
- Verify allowOrigins uses full URL format
- Ensure browser requests include proper headers

**4. Authentication blocked**
- Verify TrafficPolicy has `authConfig.disabled: true`
- Check HTTPRoute is properly targeted by policy
- Ensure gateway configuration allows the route

### Debug Commands
```bash
# Check Kubernetes resources
kubectl get pods,svc,backend,httproute,trafficpolicy -n ai-services

# Check logs
kubectl logs -n ai-services -l app=weather-mcp-dynamic -f
kubectl logs -n ai-services -l app=weather-rest-api -f

# Test connectivity
kubectl port-forward -n ai-services svc/weather-mcp-dynamic 8000:80
curl http://localhost:8000/health
```

## Technical Details

### Weather Service Implementation
- **Language**: Python 3.11+
- **Framework**: FastMCP 2.0 + FastAPI
- **Dependencies**: aiohttp, uvicorn, python-dotenv
- **Features**: Location caching, comprehensive error handling
- **Container**: Docker with uvx entrypoint for git-based installation

### MCP Protocol Integration
- **Protocol Version**: 2024-11-05
- **Transport**: HTTP with StreamableHTTP (not stdio)
- **Communication**: JSON-RPC 2.0 over HTTP
- **Client**: VS Code MCP extension with direct HTTP integration

### API Endpoints

#### MCP Mode (MCP_ONLY=true)
- **MCP Protocol**: JSON-RPC over HTTP at root path
- **Health Check**: `GET /health`

#### REST Mode (MCP_ONLY=false)  
- **Weather API**: `GET /weather?location={city}`
- **Health Check**: `GET /health`
- **OpenAPI Spec**: `GET /openapi.json`
- **API Docs**: `GET /docs`
- **Redoc**: `GET /redoc`

### Dependencies
- **Runtime**: Python 3.11+, Kubernetes, K-Gateway
- **Python Packages**: FastMCP 2.0, FastAPI, aiohttp, uvicorn
- **External APIs**: Open-Meteo (free, no API key required)
- **Infrastructure**: K-Gateway, Kubernetes Gateway API

## Summary

This project demonstrates modern MCP deployment patterns with:

- ✅ **FastMCP 2.0** - Latest MCP framework features
- ✅ **Dual deployment modes** - MCP protocol and REST API
- ✅ **Production Kubernetes** - High availability and scaling
- ✅ **K-Gateway integration** - Enterprise routing and policies
- ✅ **Backend type optimization** - Dynamic MCP vs Static REST
- ✅ **Comprehensive testing** - Automated validation and cleanup

Choose **Dynamic MCP** for MCP tool integration or **REST API** for HTTP client integration based on your use case.

## Related Documentation

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Open-Meteo API](https://open-meteo.com/)
- [K-Gateway Documentation](https://docs.kgateway.dev/)
- [Kubernetes Gateway API](https://gateway-api.sigs.k8s.io/)

## License

This project demonstrates MCP integration patterns and is provided for educational purposes.