# Kubernetes Weather Service Deployments

This directory contains multiple deployment options for the Weather MCP Server in Kubernetes with K-Gateway integration.

## Available Deployments

### 1. MCP Dynamic Deployment (RECOMMENDED)
**File:** `deploy-weather-mcp-dynamic.yml`

**Purpose:** Pure MCP protocol deployment with Dynamic Backend for proper MCP tool integration.

**Features:**
- ✅ MCP-only mode (`MCP_ONLY=true`)
- ✅ StreamableHTTP transport protocol
- ✅ Dynamic Backend with label selectors
- ✅ Proper "MCP Service" recognition in K-Gateway UI
- ✅ VS Code MCP extension integration
- ✅ GitHub Copilot tool support

**Usage:**
```bash
ansible-playbook deploy-weather-mcp-dynamic.yml
ansible-playbook deploy-weather-mcp-dynamic.yml -e test_mcp=true  # Test MCP integration
```

**Test Integration:**
```bash
# Configure VS Code MCP (.vscode/mcp.json)
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
**File:** `deploy-weather-rest-api.yml`

**Purpose:** Standard REST API deployment with Static Backend for HTTP client integration.

**Features:**
- ✅ REST-only mode (`MCP_ONLY=false`)
- ✅ FastAPI integration with OpenAPI docs
- ✅ Static Backend with explicit routing
- ✅ CORS enabled for browser access
- ✅ Interactive API documentation
- ✅ Standard HTTP protocol

**Usage:**
```bash
ansible-playbook deploy-weather-rest-api.yml
ansible-playbook deploy-weather-rest-api.yml -e test_endpoint=gateway  # Test via gateway
```

**API Endpoints:**
- Health: `http://agentgateway.mixwarecs-home.net/weather-api/health`
- Weather: `http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Paris`
- Docs: `http://agentgateway.mixwarecs-home.net/weather-api/docs`
- OpenAPI: `http://agentgateway.mixwarecs-home.net/weather-api/openapi.json`

### 3. Legacy MCP Deployment
**File:** `deploy-weather-mcp-only.yml`

**Purpose:** Original MCP deployment with Static Backend (for reference/compatibility).

**Note:** Use Dynamic MCP deployment instead for better K-Gateway integration.

### 4. Manual Manifest Deployment
**Directory:** `manifests/`

**Purpose:** Direct kubectl deployment without Ansible for development/testing.

**Usage:**
```bash
kubectl apply -f manifests/01-namespace.yaml
kubectl apply -f manifests/02-deployment.yaml
kubectl apply -f manifests/03-services.yaml
kubectl apply -f manifests/04-gateway.yaml
```

## Cleanup Scripts

Each deployment has a corresponding cleanup script:

```bash
# Clean up Dynamic MCP deployment
ansible-playbook cleanup-weather-mcp-dynamic.yml

# Clean up REST API deployment
ansible-playbook cleanup-weather-rest-api.yml

# Clean up MCP-only deployment
ansible-playbook cleanup-weather-mcp-only.yml
```

## Configuration

### Common Variables

All deployments use these common variables (edit in each file):

```yaml
# Cluster configuration
ai_namespace: "ai-services"
kgateway_namespace: "kgateway-system"
weather_image: "ghcr.io/geosp/mcp-weather:master"

# Gateway configuration  
gateway_hostname: "agentgateway.mixwarecs-home.net"
```

### Backend Type Comparison

| Deployment | Backend Type | Discovery Method | K-Gateway UI Display |
|------------|--------------|------------------|---------------------|
| **Dynamic MCP** | MCP | Label selectors | ✅ "MCP Service" |
| **REST API** | Static | Explicit host/port | ❌ "Static" |
| **Legacy MCP** | Static | Explicit host/port | ❌ "Static" |

## Architecture Diagrams

### Dynamic MCP Architecture
```
GitHub Copilot ←→ VS Code MCP Extension ←→ HTTP ←→ K-Gateway (MCP Backend)
                                                       ↓ /weather-dynamic/*
                                                   Weather Service (MCP)
                                                       ↓ HTTP
                                                   Open-Meteo API
```

### REST API Architecture  
```
HTTP Client ←→ K-Gateway (Static Backend) ←→ Weather Service (REST)
Browser           ↓ /weather-api/*              ↓ FastAPI + OpenAPI
curl, Postman     ↓                             ↓ HTTP
                  ↓                         Open-Meteo API
```

## Troubleshooting

### Check Deployment Status
```bash
# Pods
kubectl get pods -n ai-services -l app=weather-mcp-dynamic

# Services  
kubectl get svc -n ai-services -l app=weather-mcp-dynamic

# Backends
kubectl get backend -n ai-services -l app=weather-mcp-dynamic

# Routes
kubectl get httproute -n ai-services -l app=weather-mcp-dynamic
```

### Common Issues

**1. Backend not recognized as MCP type:**
```bash
kubectl describe backend weather-mcp-dynamic-backend -n ai-services
# Check: spec.type: MCP and selector labels match service
```

**2. Route not working:**
```bash
kubectl describe httproute weather-mcp-dynamic-route -n ai-services  
# Check: parentRefs match gateway and hostnames are correct
```

**3. Authentication blocked:**
```bash
kubectl get trafficpolicy weather-mcp-dynamic-policy -n ai-services -o yaml
# Verify: spec.authConfig.disabled: true
```

**4. CORS errors (REST API only):**
```bash
kubectl get trafficpolicy weather-rest-api-policy -n ai-services -o yaml
# Check: cors.allowOrigins uses full URL format (not "*")
```

### Logs
```bash
# Service logs
kubectl logs -n ai-services -l app=weather-mcp-dynamic -f

# K-Gateway logs  
kubectl logs -n kgateway-system -l app=kgateway -f
```

## Development

### Local Testing
```bash
# Port forward for direct access
kubectl port-forward -n ai-services svc/weather-mcp-dynamic 8000:80

# Test locally
curl http://localhost:8000/health
```

### Image Development
```bash
# Build and push new image
docker build -t ghcr.io/geosp/mcp-weather:dev .
docker push ghcr.io/geosp/mcp-weather:dev

# Update deployment to use dev image
# Edit weather_image variable in deployment file
```

## Best Practices

### Production Deployment
1. **Use Dynamic MCP deployment** for MCP tool integration
2. **Use specific image tags** (not `master` or `latest`)
3. **Set resource limits** appropriate for your cluster
4. **Monitor service health** and set up alerts
5. **Use staging environment** for testing changes

### Security
1. **Keep authentication disabled** only for MCP/tool endpoints
2. **Use HTTPS** in production (configure TLS in K-Gateway)
3. **Restrict CORS origins** to specific domains in REST API
4. **Use network policies** to limit pod-to-pod communication

### Scaling
1. **Start with 2 replicas** for high availability
2. **Use HPA** (Horizontal Pod Autoscaler) for auto-scaling
3. **Monitor resource usage** and adjust requests/limits
4. **Consider node affinity** for multi-zone deployments