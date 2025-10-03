# REST API Manifests

Kubernetes manifests for deploying Weather REST API with Static Backend for standard HTTP client access.

## Features

- ✅ **REST-only mode** (`MCP_ONLY=false`) with FastAPI
- ✅ **Static Backend** with explicit routing
- ✅ **OpenAPI documentation** at `/weather-api/docs`
- ✅ **CORS enabled** for browser access
- ✅ **Standard HTTP** protocol for HTTP clients
- ✅ **Interactive API docs** with Swagger UI

## Quick Deployment

```bash
# Apply manifests in order
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-service.yaml
kubectl apply -f 04-gateway.yaml

# Wait for deployment
kubectl wait --for=condition=ready pod -l app=weather-rest-api -n ai-services --timeout=300s
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

### 2. CORS Origins (Optional)

Edit the `cors.allowOrigins` section in `04-gateway.yaml` to match your application URLs.

### 3. Container Image (Optional)

Edit `02-deployment.yaml`:

```yaml
# Use specific version
image: ghcr.io/geosp/mcp-weather:v1.0.0
```

## Testing

```bash
# Check deployment
kubectl get pods -n ai-services -l app=weather-rest-api

# Check backend (should show as Static type)
kubectl get backend weather-rest-api-backend -n ai-services -o yaml

# Test endpoints (adjust hostname)
curl http://agentgateway.mixwarecs-home.net/weather-api/health
curl "http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Paris"
curl http://agentgateway.mixwarecs-home.net/weather-api/openapi.json

# Open API documentation in browser
open http://agentgateway.mixwarecs-home.net/weather-api/docs
```

## API Endpoints

After deployment, these endpoints are available:

- **Health Check:** `/weather-api/health`
- **Weather Data:** `/weather-api/weather?location=<city>`
- **OpenAPI Spec:** `/weather-api/openapi.json`
- **API Docs:** `/weather-api/docs`
- **Redoc:** `/weather-api/redoc`

## Architecture

```
HTTP Client ←→ K-Gateway (Static Backend) ←→ Weather Service (REST)
Browser           ↓ /weather-api/*             ↓ FastAPI + OpenAPI
curl, Postman     ↓                            ↓
```

## Client Examples

### curl
```bash
# Get weather for Tokyo
curl "http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Tokyo"

# Health check
curl http://agentgateway.mixwarecs-home.net/weather-api/health
```

### JavaScript/Fetch
```javascript
// Get weather data
const response = await fetch('http://agentgateway.mixwarecs-home.net/weather-api/weather?location=London');
const weather = await response.json();
console.log(weather);
```

### Python/Requests
```python
import requests

# Get weather data
response = requests.get('http://agentgateway.mixwarecs-home.net/weather-api/weather?location=Berlin')
weather = response.json()
print(weather)
```

## Cleanup

```bash
kubectl delete -f 04-gateway.yaml
kubectl delete -f 03-service.yaml
kubectl delete -f 02-deployment.yaml
kubectl delete -f 01-namespace.yaml
```