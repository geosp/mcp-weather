# Kubernetes Manifests Deployment

Direct kubectl deployment of Weather MCP Server without Ansible.

## Quick Deployment

```bash
# Apply all manifests in order
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-services.yaml
kubectl apply -f 04-gateway.yaml

# Wait for deployment to be ready
kubectl wait --for=condition=ready pod -l app=weather-mcp -n ai-services --timeout=300s
```

## Required Customization

### 1. Update Gateway References

Edit `04-gateway.yaml` to match your K-Gateway setup:

```yaml
# Update parentRefs to match your gateway
parentRefs:
- name: your-gateway-name      # ← Change this
  namespace: your-gateway-ns   # ← Change this
```

### 2. Update Container Image (Optional)

Edit `02-deployment.yaml` for specific versions:

```yaml
# Use specific version instead of master
image: ghcr.io/geosp/mcp-weather:v1.0.0
```

### 3. Adjust Resources (Optional)

Edit `02-deployment.yaml` for your cluster:

```yaml
resources:
  requests:
    cpu: 100m      # ← Reduce for smaller clusters
    memory: 256Mi  # ← Reduce for smaller clusters
  limits:
    cpu: 200m      # ← Reduce for smaller clusters
    memory: 512Mi  # ← Reduce for smaller clusters
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