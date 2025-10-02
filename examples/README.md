# MCP Weather Deployment Examples

This directory contains examples for deploying the Weather MCP Server in different environments and configurations.

## Available Examples

### Kubernetes Deployment (`kubernetes/`)

Production-grade deployment using Ansible and K-Gateway integration.

**Features:**
- ✅ High availability (2 replicas)
- ✅ Service-based routing (`/weather-service/*`)
- ✅ Authentication bypass for MCP tool access
- ✅ Health monitoring and resource limits
- ✅ Comprehensive testing and validation
- ✅ LoadBalancer for external access

**Prerequisites:**
- Kubernetes cluster with K-Gateway installed
- Ansible with `kubernetes.core` collection
- kubectl configured with cluster access
- Existing `agentgateway` HTTPRoute

**Quick Start:**
```bash
cd examples/kubernetes
# Update variables in deploy-weather-mcp.yml
ansible-playbook deploy-weather-mcp.yml
```

**What it deploys:**
1. **Weather MCP Deployment** - HTTP transport weather service
2. **Kubernetes Services** - ClusterIP + LoadBalancer
3. **K-Gateway Static Backend** - Bypasses authentication
4. **HTTPRoute** - Service-based routing with URL rewriting
5. **TrafficPolicy** - Disables auth for `/weather-service/*`

**Deployment Architecture:**
```
Client (Copilot) ←→ stdio ←→ Specbridge (Local)
                                  ↓ HTTP
                              K-Gateway
                                  ↓ /weather-service/*
                              Weather Service (K8s)
                                  ↓ HTTP
                              Open-Meteo API
```

## Deployment Pattern Comparison

| Pattern | Use Case | Complexity | Scalability | Production Ready |
|---------|----------|------------|-------------|------------------|
| **stdio Only** | Development, testing | Low | Single process | ❌ |
| **HTTP Direct** | Simple deployment | Medium | Manual scaling | ⚠️ |
| **K8s + Gateway** | Enterprise production | High | Auto-scaling | ✅ |

## Configuration Variables

### Kubernetes Example

Key variables to customize in `deploy-weather-mcp.yml`:

```yaml
# Cluster Configuration
kubeconfig_path: "{{ playbook_dir }}/../../../kubeconfig"
ai_namespace: "ai-services"
kgateway_namespace: "kgateway-system"

# Container Image
weather_image: "ghcr.io/geosp/mcp-weather:master"

# Gateway Configuration
gateway_hostname: "agentgateway.mixwarecs-home.net"
service_prefix: "/weather-service"
```

### Environment-Specific Customization

**Development Environment:**
- Use single replica
- Reduce resource limits
- Enable debug logging
- Use NodePort instead of LoadBalancer

**Staging Environment:**
- Use staging image tags
- Add staging-specific annotations
- Configure staging gateway routes

**Production Environment:**
- Use specific release tags (not `master`)
- Increase resource requests/limits
- Add monitoring and alerting
- Configure backup and disaster recovery

## Testing Deployment

### Automated Tests (Included)

The Kubernetes playbook includes comprehensive testing:

```bash
# Health check
curl http://agentgateway.mixwarecs-home.net/weather-service/health

# Weather API
curl "http://agentgateway.mixwarecs-home.net/weather-service/weather?location=Paris"

# OpenAPI specification
curl http://agentgateway.mixwarecs-home.net/weather-service/openapi.json
```

### MCP Integration Test

After deployment, test MCP integration:

1. **Download OpenAPI spec:**
   ```bash
   curl -s http://agentgateway.mixwarecs-home.net/weather-service/openapi.json > specs/weather-service.json
   ```

2. **Update MCP configuration** (`.vscode/mcp.json`):
   ```json
   {
     "servers": {
       "weather-specbridge": {
         "type": "stdio",
         "command": "/path/to/node",
         "args": ["/path/to/specbridge", "--specs", "/path/to/specs"]
       }
     }
   }
   ```

3. **Test in GitHub Copilot:**
   ```
   "What's the weather in Tokyo?"
   ```

## Troubleshooting

### Common Issues

**1. Route not accepted:**
```bash
kubectl get httproute weather-service-route -n ai-services -o yaml
# Check status.parents[].conditions for acceptance
```

**2. Service not ready:**
```bash
kubectl get pods -n ai-services -l app=weather-mcp
kubectl logs -n ai-services -l app=weather-mcp
```

**3. Authentication still required:**
```bash
kubectl get trafficpolicy disable-weather-service-auth -n ai-services -o yaml
# Verify extAuth.disable and rbac.action: Allow
```

**4. LoadBalancer IP not assigned:**
```bash
kubectl get svc weather-mcp-external -n ai-services
# Check with cloud provider load balancer configuration
```

### Debug Commands

```bash
# Check all weather-related resources
kubectl get all,httproute,backend,trafficpolicy -n ai-services -l app=weather-mcp

# Test internal connectivity
kubectl run debug --image=curlimages/curl -it --rm -- sh
curl http://weather-mcp.ai-services.svc.cluster.local/health

# Verify gateway routing
curl -v http://agentgateway.mixwarecs-home.net/weather-service/health
```

## Security Considerations

### Authentication Bypass

The Kubernetes deployment intentionally **disables authentication** for weather endpoints:

**Why?**
- MCP tools need direct API access
- Weather data is public information
- Simplifies client integration

**How?**
- Static Backend bypasses K-Gateway session management
- TrafficPolicy explicitly disables extAuth and sets RBAC to Allow
- Only affects `/weather-service/*` routes

**Security Boundary:**
```
┌─────────────────────────┐
│ Authenticated Routes    │  ← Normal K-Gateway auth
│ /api/*, /admin/*, etc.  │
└─────────────────────────┘
┌─────────────────────────┐
│ Public Tool Routes      │  ← Authentication bypassed
│ /weather-service/*      │
│ /other-tool-service/*   │
└─────────────────────────┘
```

### Production Security

For production deployments, consider:

- **Network policies** to restrict pod-to-pod communication
- **Resource quotas** to prevent resource exhaustion
- **Pod security standards** for container security
- **Service mesh** for additional traffic encryption
- **Monitoring** for suspicious usage patterns

## Contributing Examples

To add new deployment examples:

1. Create subdirectory under `examples/`
2. Include comprehensive README
3. Add configuration templates
4. Document prerequisites and testing
5. Update this main examples README

### Example Structure
```
examples/
├── README.md (this file)
├── new-deployment-type/
│   ├── README.md
│   ├── deploy.yml
│   ├── config/
│   └── tests/
```