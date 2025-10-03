# Kubernetes Manifests Deployment

Direct kubectl deployment of Weather MCP Server without Ansible.

## Overview

This directory provides two sets of Kubernetes manifests for deploying the Weather service:

### 1. MCP Dynamic (`mcp-dynamic/`) - **RECOMMENDED**
- **Purpose:** MCP tool integration (VS Code, GitHub Copilot)
- **Backend Type:** Dynamic MCP with label selectors
- **Protocol:** StreamableHTTP (proper MCP transport)
- **Recognition:** Shows as "MCP Service" in K-Gateway UI
- **Client:** VS Code MCP extension, MCP tools

### 2. REST API (`rest-api/`)
- **Purpose:** HTTP client integration (browsers, curl, apps)
- **Backend Type:** Static with explicit routing
- **Protocol:** Standard HTTP
- **Recognition:** Shows as "Static" in K-Gateway UI
- **Client:** HTTP clients, browsers, REST APIs

### 3. Legacy (`01-namespace.yaml`, `02-deployment.yaml`, etc.)
- **Purpose:** Original manifests (for compatibility)
- **Note:** Consider migrating to specific mcp-dynamic/ or rest-api/ sets

## Quick Deployment

### Option A: MCP Dynamic (Recommended for MCP tools)
```bash
cd mcp-dynamic/
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-service.yaml
kubectl apply -f 04-gateway.yaml

# Wait for deployment to be ready
kubectl wait --for=condition=ready pod -l app=weather-mcp-dynamic -n ai-services --timeout=300s
```

### Option B: REST API (For HTTP clients)
```bash
cd rest-api/
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-service.yaml
kubectl apply -f 04-gateway.yaml

# Wait for deployment to be ready
kubectl wait --for=condition=ready pod -l app=weather-rest-api -n ai-services --timeout=300s
```

## Comparison

| Feature | MCP Dynamic | REST API | Legacy |
|---------|-------------|----------|--------|
| **Backend Type** | MCP | Static | Static |
| **Discovery** | Label selectors | Explicit host | Explicit host |
| **K-Gateway UI** | ✅ "MCP Service" | ❌ "Static" | ❌ "Static" |
| **Protocol** | StreamableHTTP | HTTP | HTTP |
| **VS Code Integration** | ✅ Direct | ❌ No | ❌ No |
| **API Documentation** | ❌ No | ✅ OpenAPI/Swagger | ❌ No |
| **CORS Support** | ❌ No | ✅ Yes | ❌ No |

## Required Customization

Both deployment options require the same basic customization:

### 1. Update Gateway References

Edit the `04-gateway.yaml` file in your chosen directory:

```yaml
# Update parentRefs to match your gateway
parentRefs:
- name: agentgateway           # ← Change to your gateway name
  namespace: kgateway-system   # ← Change to your gateway namespace

# Update hostname to match your domain
hostnames:
- agentgateway.mixwarecs-home.net  # ← Change to your domain
```

### 2. Update Container Image (Optional)

Edit the `02-deployment.yaml` file:

```yaml
# Use specific version instead of master
image: ghcr.io/geosp/mcp-weather:v1.0.0
```

### 3. Adjust Resources (Optional)

Edit the `02-deployment.yaml` file for your cluster:

```yaml
resources:
  requests:
    cpu: 100m      # ← Reduce for smaller clusters
    memory: 256Mi  # ← Reduce for smaller clusters
  limits:
    cpu: 200m      # ← Reduce for smaller clusters
    memory: 512Mi  # ← Reduce for smaller clusters
```

## Testing

### MCP Dynamic Testing
```bash
# Check deployment
kubectl get pods -n ai-services -l app=weather-mcp-dynamic

# Check backend (should be MCP type)
kubectl get backend weather-mcp-dynamic-backend -n ai-services -o yaml

# Test health endpoint (adjust hostname)
curl http://agentgateway.mixwarecs-home.net/weather-dynamic/health

# VS Code integration (.vscode/mcp.json)
{
  "servers": {
    "weather-dynamic-http": {
      "type": "http",
      "url": "http://agentgateway.mixwarecs-home.net/weather-dynamic/"
    }
  }
}
```

### REST API Testing
```bash
# Check deployment
kubectl get pods -n ai-services -l app=weather-rest-api

# Check backend (should be Static type)
kubectl get backend weather-rest-api-backend -n ai-services -o yaml

# Test endpoints (adjust hostname)
curl http://agentgateway.mixwarecs-home.net/weather-api/health
curl "http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Paris"
curl http://agentgateway.mixwarecs-home.net/weather-api/openapi.json

# API documentation
open http://agentgateway.mixwarecs-home.net/weather-api/docs
```

## Choosing the Right Deployment

### Use MCP Dynamic When:
- ✅ Integrating with VS Code MCP extension
- ✅ Using GitHub Copilot tools
- ✅ Building MCP-aware applications
- ✅ Want proper "MCP Service" recognition in K-Gateway UI
- ✅ Need MCP protocol features

### Use REST API When:
- ✅ Building web applications or mobile apps
- ✅ Need OpenAPI documentation and Swagger UI
- ✅ Integrating with existing HTTP/REST clients
- ✅ Want CORS support for browser access
- ✅ Need standard HTTP API patterns

## Limitations vs Ansible Deployments

Compared to the Ansible playbooks, these manual manifests:

- ❌ **No automated testing** and validation
- ❌ **No cleanup automation** (manual kubectl delete required)
- ❌ **No environment customization** (must edit files manually)
- ❌ **No deployment status reporting**
- ❌ **No integrated health checks**

**For production use, consider the Ansible playbooks:**
- `../deploy-weather-mcp-dynamic.yml` - Automated Dynamic MCP deployment
- `../deploy-weather-rest-api.yml` - Automated REST API deployment

## Cleanup

### MCP Dynamic Cleanup
```bash
cd mcp-dynamic/
kubectl delete -f 04-gateway.yaml
kubectl delete -f 03-service.yaml
kubectl delete -f 02-deployment.yaml
kubectl delete -f 01-namespace.yaml
```

### REST API Cleanup
```bash
cd rest-api/
kubectl delete -f 04-gateway.yaml
kubectl delete -f 03-service.yaml
kubectl delete -f 02-deployment.yaml
kubectl delete -f 01-namespace.yaml
```

### Legacy Cleanup
```bash
kubectl delete -f 04-gateway.yaml
kubectl delete -f 03-services.yaml
kubectl delete -f 02-deployment.yaml
kubectl delete -f 01-namespace.yaml
```

## Troubleshooting

### Common Issues

**1. Route not accepted:**
```bash
# Check HTTPRoute status
kubectl describe httproute <route-name> -n ai-services
# Verify parentRefs match your gateway configuration
```

**2. Backend not recognized:**
```bash
# For MCP Dynamic
kubectl describe backend weather-mcp-dynamic-backend -n ai-services
# Check: spec.type: MCP and selector labels match service

# For REST API  
kubectl describe backend weather-rest-api-backend -n ai-services
# Check: spec.static.hosts points to correct service FQDN
```

**3. Authentication blocked:**
```bash
kubectl get trafficpolicy <policy-name> -n ai-services -o yaml
# Ensure authConfig.disabled: true is set
```

**4. CORS errors (REST API only):**
```bash
kubectl get trafficpolicy weather-rest-api-policy -n ai-services -o yaml
# Check cors.allowOrigins uses full URL format
```

### Logs
```bash
# Service logs (adjust app label)
kubectl logs -n ai-services -l app=weather-mcp-dynamic -f
kubectl logs -n ai-services -l app=weather-rest-api -f

# K-Gateway logs
kubectl logs -n kgateway-system -l app=kgateway -f
```
```

## Testing

After deployment, test the service:

```bash
# Check pod status
kubectl get pods -n ai-services -l app=weather-mcp

# Check service
kubectl get svc -n ai-services weather-mcp

# Check backend and route
kubectl get backend,httproute -n ai-services

# Test health endpoint (adjust hostname to your setup)
curl http://agentgateway.mixwarecs-home.net/weather-service/health

# Test weather API
curl "http://agentgateway.mixwarecs-home.net/weather-service/weather?location=Paris"
```

## Architecture

This manual deployment creates:

```
HTTP Client ←→ K-Gateway ←→ Static Backend ←→ Weather Service
                ↓ /weather-service/*           ↓ HTTP transport
                                            Open-Meteo API
```

**Note:** This uses a Static Backend configuration, which means:
- K-Gateway UI will show it as "Static" not "MCP Service"
- Uses explicit host/port routing instead of service discovery
- Good for development/testing but consider Dynamic MCP for production

## Limitations

Compared to the Ansible deployments, this manual approach:

- ❌ No automated testing and validation
- ❌ No cleanup automation
- ❌ Single deployment option (Static Backend only)
- ❌ Manual configuration required
- ❌ No environment-specific customization

For production use, consider the Ansible playbooks:
- `../deploy-weather-mcp-dynamic.yml` - Dynamic MCP Backend (recommended)
- `../deploy-weather-rest-api.yml` - REST API with Static Backend

## Cleanup

```bash
# Remove all resources
kubectl delete -f 04-gateway.yaml
kubectl delete -f 03-services.yaml
kubectl delete -f 02-deployment.yaml
kubectl delete -f 01-namespace.yaml
```

## Troubleshooting

### Common Issues

**1. Route not accepted:**
```bash
kubectl describe httproute weather-service-route -n ai-services
# Check parentRefs match your gateway configuration
```

**2. Service not reachable:**
```bash
kubectl describe backend weather-service-backend -n ai-services
# Verify static.hosts points to correct service FQDN
```

**3. Authentication required:**
```bash
kubectl get trafficpolicy weather-service-policy -n ai-services -o yaml
# Ensure authConfig.disabled: true is set
```

### Logs

```bash
# Service logs
kubectl logs -n ai-services -l app=weather-mcp -f

# K-Gateway logs
kubectl logs -n kgateway-system -l app=kgateway -f
```
```

## Verification

### Check Deployment Status

```bash
# Check all resources
kubectl get all -n ai-services -l app=weather-mcp

# Check gateway resources
kubectl get httproute,backend,trafficpolicy -n ai-services -l app=weather-mcp

# Check pod logs
kubectl logs -n ai-services -l app=weather-mcp
```

### Test Endpoints

```bash
# Get LoadBalancer IP
EXTERNAL_IP=$(kubectl get svc weather-mcp-external -n ai-services -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test direct access
curl http://$EXTERNAL_IP:8000/health
curl "http://$EXTERNAL_IP:8000/weather?location=Paris"

# Test through gateway (update hostname)
curl http://your-gateway-hostname/weather-service/health
curl "http://your-gateway-hostname/weather-service/weather?location=Paris"
curl http://your-gateway-hostname/weather-service/openapi.json
```

## Cleanup

```bash
# Remove all resources
kubectl delete -f 04-gateway.yaml
kubectl delete -f 03-services.yaml
kubectl delete -f 02-deployment.yaml
kubectl delete -f 01-namespace.yaml
```

## Differences from Ansible Deployment

| Feature | Ansible Playbook | Kubectl Manifests |
|---------|------------------|-------------------|
| **Validation** | Automated waiting and testing | Manual verification |
| **Customization** | Variables and templates | Direct YAML editing |
| **Error Handling** | Retry logic and rollback | Manual troubleshooting |
| **Testing** | Integrated test jobs | Manual curl commands |
| **Prerequisites** | Automated checks | Manual validation |

## When to Use

**Use kubectl manifests when:**
- Simple one-time deployment
- GitOps workflow (ArgoCD, Flux)
- Learning Kubernetes resources
- CI/CD pipeline integration

**Use Ansible playbook when:**
- Production deployment with validation
- Complex environment management
- Automated testing and rollback
- Infrastructure as Code practices