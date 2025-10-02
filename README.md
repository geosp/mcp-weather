# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather tools by bridging a REST weather service to MCP clients through OpenAPI specification conversion using Specbridge.

## Overview

This project demonstrates a complete MCP weather integration with two main components:
1. **FastMCP Weather Service** - A Python-based weather API using Open-Meteo data
2. **Specbridge MCP Bridge** - Converts the deployed weather service to MCP tools

## Project Architecture

```
MCP Client (AI Assistant) ←→ GitHub Copilot
    ↓ (stdio via mcp.json)
Specbridge MCP Server (Node.js)
    ↓ (HTTP REST)
Deployed Weather Service API (FastMCP/Python)
    ↓ (API calls)
Open-Meteo Weather Data (External API)
```

## Project Structure

```
mcp-weather/
├── README.md                      # This documentation
├── .vscode/
│   └── mcp.json                   # MCP client configuration for Copilot
├── specs/
│   └── weather-service.json       # OpenAPI spec downloaded from service
├── mcp_weather/                   # Python FastMCP weather service source
│   ├── __init__.py
│   └── weather.py                 # Main weather service implementation
├── examples/                      # Deployment examples
│   ├── README.md                  # Examples overview
│   └── kubernetes/                # Kubernetes deployment examples
│       ├── deploy-weather-mcp.yml # Ansible playbook (full automation)
│       └── manifests/             # kubectl YAML files (manual deployment)
├── pyproject.toml                 # Python dependencies and build config
├── Dockerfile                     # Container for deploying weather service
├── .github/workflows/
│   └── docker-publish.yml         # CI/CD for container deployment
├── uv.lock                        # Python dependency lock file
└── specbridge.log                 # MCP server logs
```

## MCP Transport Concepts

The Model Context Protocol (MCP) supports different transport mechanisms for client-server communication. Understanding these is crucial for deployment architecture:

### Transport Types

#### 1. **stdio (Standard Input/Output)**
- **Use Case**: Direct client integration (GitHub Copilot, VS Code, Claude Desktop)
- **Communication**: Process spawning with stdin/stdout pipes
- **Protocol**: JSON-RPC over stdio streams
- **Example**: Specbridge running as MCP server for Copilot
- **Benefits**: Simple setup, process isolation, direct control
- **Configuration**: 
  ```json
  {
    "type": "stdio",
    "command": "/path/to/node",
    "args": ["/path/to/specbridge", "--specs", "/specs/dir"]
  }
  ```

#### 2. **HTTP Transport**
- **Use Case**: Service deployments, production environments, multiple clients
- **Communication**: HTTP REST API endpoints
- **Protocol**: JSON-RPC over HTTP
- **Example**: Weather service deployed on Kubernetes
- **Benefits**: Scalability, load balancing, standard web infrastructure
- **Configuration**:
  ```yaml
  args: ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
  ```

### Our Hybrid Architecture

This project demonstrates **both transport patterns**:

```
MCP Client (Copilot) ←→ stdio ←→ Specbridge (Local Process)
                                      ↓ HTTP REST
                              Weather Service (Kubernetes)
                                      ↓ HTTP API
                              Open-Meteo (External API)
```

**Why this hybrid approach?**
1. **Client Integration**: stdio for direct MCP protocol with Copilot
2. **Service Deployment**: HTTP for scalable, production-ready weather API
3. **Protocol Bridge**: Specbridge converts HTTP REST → MCP tools
4. **Flexibility**: Can swap weather backends without changing MCP client

## Components

### 1. FastMCP Weather Service (Python)
- **Source**: `mcp_weather/weather.py`
- **Framework**: FastMCP + FastAPI
- **Transport**: **HTTP** (deployed as web service)
- **Data Source**: Open-Meteo API (no API key required)
- **Deployment**: `http://agentgateway.mixwarecs-home.net/weather-service`
- **Features**: Location caching, comprehensive weather data, error handling
- **Container**: Kubernetes deployment with 2 replicas, health checks, load balancing

### 2. Specbridge MCP Bridge (Node.js)
- **Purpose**: Converts REST API to MCP tools via OpenAPI specs
- **Transport**: **stdio** (spawned by MCP client)
- **Installation**: `npm install -g specbridge`
- **Version**: 1.0.2
- **Process Model**: Local process managed by VS Code/Copilot
- **Communication**: JSON-RPC over stdin/stdout to HTTP REST calls

### 3. OpenAPI Specification
- **File**: `specs/weather-service.json`
- **Source**: Auto-downloaded from deployed service
- **Enhancement**: Added proper server URL for Specbridge integration
- **Purpose**: Enables automatic tool generation from REST endpoints

## Deployment Architecture

### Kubernetes Production Deployment

The Ansible playbook you referenced demonstrates a **production-grade deployment** with multiple infrastructure components:

#### Service Infrastructure Components

1. **Weather MCP Container**
   ```yaml
   # HTTP Transport Configuration
   args: ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
   ```
   - **Transport**: HTTP for scalable web service
   - **Replicas**: 2 for high availability  
   - **Health Checks**: Liveness and readiness probes
   - **Resource Limits**: CPU/memory constraints for stability

2. **Kubernetes Services**
   ```yaml
   # Internal ClusterIP for cluster communication
   weather-mcp.ai-services.svc.cluster.local:80
   
   # External LoadBalancer for direct access
   LoadBalancer IP:8000
   ```

3. **K-Gateway Integration** (Key Innovation)
   ```yaml
   # Static Backend - Bypasses Authentication
   type: Static
   hosts: weather-mcp.ai-services.svc.cluster.local:80
   ```

#### Service-Based Routing Pattern

**Why Service-Based Routes?**
Traditional API routing exposes individual endpoints:
```
/weather → weather endpoint
/health → health endpoint  
/openapi.json → spec endpoint
```

**Service-based routing** groups related endpoints under a service prefix:
```
/weather-service/weather → weather endpoint
/weather-service/health → health endpoint
/weather-service/openapi.json → spec endpoint
```

**Benefits:**
- **Namespace Isolation**: Multiple services can coexist
- **Gateway Management**: Single route rule handles all endpoints
- **Authentication Scope**: Policies apply to entire service
- **Service Discovery**: Clear service boundaries for tools

#### Authentication Bypass Strategy

**The Problem**: K-Gateway typically requires session management and authentication for all routes.

**The Solution**: Static Backend + TrafficPolicy
```yaml
# 1. Static Backend bypasses session management
spec:
  type: Static  # Key: No dynamic backend resolution
  static:
    hosts: [weather-mcp.ai-services.svc.cluster.local:80]

# 2. TrafficPolicy disables authentication
spec:
  extAuth:
    disable: {}  # Key: Explicitly disable auth
  rbac:
    action: Allow
    policy:
      matchExpressions: ["true"]  # Allow all requests
```

**Why This Works:**
- **Static Backend**: Bypasses K-Gateway's normal session management pipeline
- **Disabled ExtAuth**: No external authentication required
- **Open RBAC**: Allow policy for all requests
- **Service Isolation**: Only affects `/weather-service/*` routes

### Transport Protocol Flow

```
GitHub Copilot Chat
    ↓ (stdio JSON-RPC)
Specbridge MCP Server (Local Node.js Process)
    ↓ (HTTP REST)
K-Gateway (agentgateway.mixwarecs-home.net)
    ↓ (/weather-service/* → Static Backend)
Weather Service (Kubernetes Pod)
    ↓ (HTTP API)
Open-Meteo Weather API (External)
```

**Key Transport Decisions:**
1. **Client → Specbridge**: stdio for direct MCP integration
2. **Specbridge → Gateway**: HTTP for standard web protocols
3. **Gateway → Service**: HTTP with service discovery
4. **Service → External**: HTTP for weather data

### Ansible Deployment Phases Explained

The Ansible playbook demonstrates a **10-phase deployment strategy** for production MCP services:

#### Phase 0: Prerequisites
- Validates kubeconfig exists
- Ensures cluster connectivity

#### Phase 1: Core Service Deployment
```yaml
# HTTP Transport Weather Service
containers:
  - name: weather-mcp
    command: ["uvx"]
    args: ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
```
- **Why HTTP?** Enables load balancing, health checks, multiple replicas
- **Why uvx?** Zero-dependency Python execution from git repository
- **Production Features**: Resource limits, health probes, monitoring annotations

#### Phase 2: Service Discovery
```yaml
# ClusterIP for internal communication
Service: weather-mcp.ai-services.svc.cluster.local:80

# LoadBalancer for external access
Service: External IP:8000
```
- **Internal**: Cluster DNS resolution for K-Gateway
- **External**: Direct access for testing and development

#### Phase 3: K-Gateway Static Backend
```yaml
type: Static
static:
  hosts: [weather-mcp.ai-services.svc.cluster.local:80]
```
- **Critical Design**: Bypasses K-Gateway session management
- **No Authentication**: Static backends skip normal auth pipeline
- **Direct Routing**: Routes directly to service without user context

#### Phase 4: Service-Based HTTPRoute
```yaml
rules:
  - matches:
      - path: 
          type: PathPrefix
          value: /weather-service  # Service prefix
    filters:
      - type: URLRewrite
        urlRewrite:
          path:
            replacePrefixMatch: /  # Strip prefix before forwarding
```
- **URL Transformation**: `/weather-service/weather` → `/weather`
- **Prefix Matching**: All `/weather-service/*` routes handled
- **Gateway Integration**: Attaches to existing agentgateway

#### Phase 5: Authentication Disable
```yaml
TrafficPolicy:
  extAuth:
    disable: {}  # Disable external auth
  rbac:
    action: Allow
    policy:
      matchExpressions: ["true"]  # Allow all
```
- **Complete Bypass**: No authentication or authorization required
- **Open Access**: Essential for MCP tool integration
- **Scoped Policy**: Only affects weather service routes

#### Phase 6-7: Validation & Readiness
- **Route Acceptance**: Waits for K-Gateway to accept routes
- **Deployment Ready**: Ensures all replicas are healthy
- **LoadBalancer**: Waits for external IP assignment

#### Phase 8: Integration Testing
```bash
# Service-based endpoint testing
curl http://agentgateway.mixwarecs-home.net/weather-service/weather?location=Atlanta
curl http://agentgateway.mixwarecs-home.net/weather-service/health
curl http://agentgateway.mixwarecs-home.net/weather-service/openapi.json
```
- **Comprehensive Validation**: Tests all endpoints through gateway
- **Retry Logic**: Handles service startup timing
- **End-to-end**: Validates complete request path

#### Phase 9: Cleanup Legacy Resources
- Removes old individual route configurations
- Cleans up outdated authentication policies
- Ensures clean service-based deployment

#### Phase 10: Production Summary
- **Service Endpoints**: All `/weather-service/*` routes documented
- **LoadBalancer Info**: External access details provided
- **Test Commands**: Ready-to-use validation commands

### Why This Deployment Pattern Works for MCP

1. **HTTP Service Layer**: Weather service runs as standard web service
   - Kubernetes native (pods, services, ingress)
   - Standard monitoring and logging
   - Horizontal scaling capabilities

2. **Gateway Integration**: K-Gateway provides enterprise features
   - Service routing and discovery
   - Traffic policies and rate limiting
   - Authentication bypass for public tools

3. **MCP Bridge Layer**: Specbridge converts HTTP → MCP
   - No changes needed to weather service
   - Automatic tool generation from OpenAPI
   - stdio transport for direct client integration

4. **Client Integration**: Standard MCP protocol
   - Works with any MCP client (Copilot, Claude, etc.)
   - No weather service deployment details exposed
   - Simple configuration via `mcp.json`

### MCP Transport Design Decisions

#### Hybrid Architecture Rationale

**Question**: Why not use MCP stdio transport end-to-end?

**Answer**: Different transport types optimize for different requirements:

| Requirement | stdio Transport | HTTP Transport |
|-------------|----------------|----------------|
| **Client Integration** | ✅ Direct MCP protocol | ❌ Requires HTTP→MCP bridge |
| **Service Deployment** | ❌ Process management complexity | ✅ Standard web deployment |
| **Load Balancing** | ❌ Single process per client | ✅ Multiple replicas, load balancer |
| **Health Monitoring** | ❌ Process lifecycle only | ✅ HTTP health checks, metrics |
| **Service Discovery** | ❌ Manual process management | ✅ Kubernetes DNS, service mesh |
| **Authentication** | ❌ Process-level security | ✅ Gateway policies, RBAC |
| **Development** | ✅ Simple local testing | ❌ Requires service deployment |
| **Production Ops** | ❌ Custom process monitoring | ✅ Standard container orchestration |

#### Transport Selection Guidelines

**Use stdio MCP when:**
- Direct client integration (Copilot, Claude Desktop)
- Simple development and testing
- Single-user or local scenarios
- Custom MCP protocol features needed

**Use HTTP MCP when:**
- Production service deployment
- Multiple clients or high availability
- Standard web infrastructure integration
- Enterprise security and monitoring requirements

**Use Hybrid (Our Approach) when:**
- Need both client integration AND service deployment
- Want to leverage existing HTTP services as MCP tools
- Require production-grade service deployment with MCP clients
- Converting existing REST APIs to MCP without rewriting

#### Alternative Architecture Patterns

**Pattern 1: Pure stdio MCP**
```
Copilot ←→ stdio ←→ MCP Weather Server (Local Process)
                         ↓ HTTP
                   Open-Meteo API
```
- **Pros**: Simple MCP setup, direct protocol
- **Cons**: No service deployment, single process, manual scaling

**Pattern 2: Pure HTTP MCP**
```
Copilot ←→ HTTP ←→ MCP Weather Server (Web Service)
                         ↓ HTTP  
                   Open-Meteo API
```
- **Pros**: Standard web deployment, full production features
- **Cons**: MCP client needs HTTP transport support, more complex

**Pattern 3: Hybrid (Our Choice)**
```
Copilot ←→ stdio ←→ Specbridge ←→ HTTP ←→ Weather Service
                                           ↓ HTTP
                                     Open-Meteo API
```
- **Pros**: Best of both worlds, existing service integration, production ready
- **Cons**: Additional component (Specbridge), slightly more complex

### Production Considerations

#### Security Implications
- **stdio Transport**: Process-level isolation, no network exposure
- **HTTP Transport**: Network security, authentication, authorization required
- **Hybrid**: stdio isolation for client + HTTP security for service layer

#### Scaling Patterns
- **stdio**: One process per MCP client connection
- **HTTP**: Horizontal scaling, load balancing, replica management
- **Hybrid**: Client processes scale independently from service replicas

#### Monitoring and Observability
- **stdio**: Process logs, limited metrics
- **HTTP**: Full HTTP metrics, health checks, distributed tracing
- **Hybrid**: Both process monitoring and service observability

### MCP Deployment Ecosystem

#### Deployment Pattern Summary

Your Ansible playbook demonstrates **Enterprise MCP Integration** - converting existing production services into MCP tools:

```yaml
# Key Pattern: HTTP MCP Service + Gateway Integration
weather_image: "ghcr.io/geosp/mcp-weather:master"
command: ["uvx"]
args: ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]

# Key Pattern: Authentication Bypass for Tool Access
extAuth:
  disable: {}  # Essential for MCP tool integration
rbac:
  action: Allow
```

### 🎯 **Critical Discovery: REST API vs MCP Protocol Compatibility**

During development and testing, we discovered an **important limitation** in the FastMCP framework regarding simultaneous REST API and MCP protocol support:

#### **The Issue**
When attempting to serve both REST API endpoints and MCP protocol from the same FastAPI application:

- ✅ **REST API works** when MCP app is mounted at `/mcp` 
- ❌ **MCP protocol fails** with "Session terminated" errors when mounted
- ✅ **MCP protocol works** only in `MCP_ONLY=true` mode (pure MCP app)

#### **Root Cause**
The FastMCP HTTP application has specific requirements for:
- Session management and lifespan handling
- WebSocket/HTTP upgrade handling  
- Protocol-specific middleware

When mounted as a sub-application in FastAPI, these mechanisms get interfered with, causing the MCP protocol handshake to fail.

#### **Production Solution: Dual Service Architecture**

For maximum reliability, deploy **two separate services**:

##### **Service 1: REST API Service** 
```bash
# Standard web API on port 3000
MCP_TRANSPORT=http MCP_PORT=3000 uv run python -m mcp_weather.weather
```
**Endpoints:**
- ✅ `/weather?location=city` - REST API for web clients
- ✅ `/health` - Health checks for monitoring
- ✅ `/docs` - OpenAPI documentation
- ✅ `/` - Service information

##### **Service 2: Pure MCP Protocol Service**
```bash
# Pure MCP protocol on port 3001  
MCP_TRANSPORT=http MCP_PORT=3001 MCP_ONLY=true uv run python -m mcp_weather.weather
```
**Features:**
- ✅ Pure MCP JSON-RPC protocol for AI assistants
- ✅ Clean session management without mounting complications
- ✅ Dedicated port for MCP clients

#### **Kubernetes Deployment Strategy**

```yaml
# REST API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-api
spec:
  template:
    spec:
      containers:
      - name: weather-api
        env:
        - name: MCP_TRANSPORT
          value: "http"
        - name: MCP_PORT
          value: "3000"
        # MCP_ONLY defaults to false = REST API mode

---
# MCP Protocol Deployment  
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-mcp
spec:
  template:
    spec:
      containers:
      - name: weather-mcp
        env:
        - name: MCP_TRANSPORT
          value: "http"
        - name: MCP_PORT
          value: "3001"
        - name: MCP_ONLY
          value: "true"
        # Pure MCP protocol mode
```

#### **Benefits of Dual Service Architecture**

1. **🔒 Reliability**: Each service optimized for its specific protocol
2. **📈 Scaling**: Independent scaling based on usage patterns
3. **🛡️ Isolation**: Issues in one service don't affect the other
4. **🔧 Maintenance**: Simpler debugging and service management
5. **🌐 Flexibility**: Different clients can use appropriate endpoints

#### **Alternative: Current Hybrid Approach**

The current implementation uses Specbridge as a bridge:
```
AI Client ←(MCP)→ Specbridge ←(HTTP REST)→ Weather Service
```

This works well because:
- ✅ REST API service focuses on HTTP
- ✅ Specbridge handles MCP protocol conversion
- ✅ No mounting complications within FastMCP
- ✅ Production-tested architecture

#### When to Use This Pattern

**✅ Use HTTP MCP + Gateway Integration when:**
- Converting existing REST services to MCP tools
- Need production-grade deployment (HA, monitoring, scaling)
- Multiple MCP clients will access the same service
- Enterprise infrastructure with API gateways
- Compliance requirements for service deployment
- Want to expose services to both MCP and traditional HTTP clients

**❌ Don't use this pattern when:**
- Simple development or personal use cases
- Single MCP client scenarios
- Services don't need high availability
- Prefer simpler stdio deployment

#### Comparison with Other MCP Patterns

**1. Traditional stdio MCP (Simple)**
```json
// .mcp.json
{
  "servers": {
    "weather": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp_weather"]
    }
  }
}
```
- **Use Case**: Development, single-user, simple tools
- **Deployment**: Local process execution
- **Scaling**: One process per client

**2. HTTP MCP Direct (Intermediate)**
```json
// .mcp.json  
{
  "servers": {
    "weather": {
      "type": "http",
      "endpoint": "http://localhost:8000/mcp"
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

## Technical Details

### Weather Service Implementation
- **Language**: Python 3.11+
- **Framework**: FastMCP + FastAPI  
- **Dependencies**: aiohttp, uvicorn, python-dotenv
- **Features**: Location caching, comprehensive error handling
- **Container**: Docker with uvx entrypoint

### MCP Protocol Integration
- **Protocol Version**: 2024-11-05
- **Transport**: stdio (JSON-RPC over stdin/stdout)
- **Communication**: JSON-RPC 2.0
- **Client**: GitHub Copilot with mcp.json configuration

### API Endpoints
- `GET /weather?location={city}` - Get weather data
- `GET /health` - Health check
- `GET /openapi.json` - OpenAPI specification  
- `GET /` - API information

### Dependencies
- **Runtime**: Node.js v24.9.0, Python 3.11+
- **MCP Bridge**: Specbridge 1.0.2
- **Python Packages**: FastMCP, FastAPI, aiohttp, uvicorn
- **External APIs**: Open-Meteo (free, no API key)

## Deployment

### Container Deployment
```bash
docker build -t mcp-weather .
docker run -p 3000:3000 mcp-weather mcp-weather
```

### CI/CD
- **Workflow**: `.github/workflows/docker-publish.yml`
- **Registry**: GitHub Container Registry
- **Trigger**: Push to main branch

## Related Documentation

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Specbridge GitHub](https://github.com/modelcontextprotocol/specbridge)  
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Open-Meteo API](https://open-meteo.com/)
- [GitHub Copilot Extensions](https://docs.github.com/en/copilot)

## License

This project demonstrates MCP integration patterns and is provided for educational purposes.