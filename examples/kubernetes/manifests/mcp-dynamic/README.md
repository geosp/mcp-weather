# MCP Dynamic Manifests

Kubernetes manifests for deploying Weather MCP Server with Dynamic Backend for proper MCP tool integration.

## Features

- ✅ **MCP-only mode** (`MCP_ONLY=true`) for pure protocol
- ✅ **Dynamic Backend** with label selectors for auto-discovery
- ✅ **StreamableHTTP** transport protocol
- ✅ **MCP Service recognition** in K-Gateway UI
- ✅ **VS Code MCP extension** integration
- ✅ **GitHub Copilot** tool support

## Quick Deployment

```bash
# Apply manifests in order
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-service.yaml
kubectl apply -f 04-gateway.yaml

# Wait for deployment
kubectl wait --for=condition=ready pod -l app=weather-mcp-dynamic -n ai-services --timeout=300s
```

## Customization Required

### 1. Gateway Configuration

Edit `04-gateway.yaml`:

```yaml
# Update parentRefs to match your gateway
parentRefs:
- name: agentgateway           # ← Your gateway name
  namespace: kgateway-system   # ← Your gateway namespace

# Update hostname to match your domain
hostnames:
- agentgateway.mixwarecs-home.net  # ← Your domain
```

### 2. Container Image (Optional)

Edit `02-deployment.yaml`:

```yaml
# Use specific version
image: ghcr.io/geosp/mcp-weather:v1.0.0
```

## Testing

```bash
# Check deployment
kubectl get pods -n ai-services -l app=weather-mcp-dynamic

# Check backend (should show as MCP type)
kubectl get backend weather-mcp-dynamic-backend -n ai-services -o yaml

# Test health (adjust hostname)
curl http://agentgateway.mixwarecs-home.net/weather-dynamic/health
```

## VS Code Integration

Add to `.vscode/mcp.json`:

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

## Architecture

```
GitHub Copilot ←→ VS Code MCP ←→ HTTP ←→ K-Gateway (MCP Backend)
                                          ↓ /weather-dynamic/*
                                      Weather Service (MCP)
```

## Cleanup

```bash
kubectl delete -f 04-gateway.yaml
kubectl delete -f 03-service.yaml
kubectl delete -f 02-deployment.yaml
kubectl delete -f 01-namespace.yaml
```