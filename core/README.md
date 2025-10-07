# Core Infrastructure

This directory contains reusable infrastructure components that can be shared across multiple projects.

## Components

### 1. Authentication

- **auth.py**: FastAPI authentication dependencies for Bearer token validation with Authentik
- **authentik_client.py**: Client for interacting with Authentik API
- **auth_provider.py**: Base MCP authentication providers for FastMCP integration

### 2. Configuration

- **config.py**: Base configuration classes for common settings like:
  - Authentication settings
  - Cache settings
  - Server settings

## Usage

### Authentication

```python
# Get a ready-to-use Authentik auth provider
from core.auth_provider import get_auth_provider
auth_provider = get_auth_provider("my-service")

# Or create a new instance
from core.auth_provider import create_auth_provider
auth_provider = create_auth_provider("my-service")

# Use with FastMCP
from fastmcp import FastMCP
mcp = FastMCP("my-service", auth=auth_provider)
```

### Configuration

```python
# Extend base configuration classes
from core.config import BaseServerConfig

class MyServerConfig(BaseServerConfig):
    # Add custom fields
    debug_mode: bool = False
    
    @classmethod
    def from_env(cls):
        config = super().from_env(env_prefix="MY_APP_")
        config.debug_mode = os.getenv("MY_APP_DEBUG", "false").lower() == "true"
        return config
```

## Design Principles

1. **Reusability**: Components should be designed for reuse across projects
2. **Extensibility**: Base classes and interfaces should be easy to extend
3. **Separation of Concerns**: Clear boundaries between different components
4. **Consistency**: Common patterns and interfaces for similar tasks
5. **Documentation**: Clear documentation for all components