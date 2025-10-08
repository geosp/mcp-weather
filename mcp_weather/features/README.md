# Feature-Based Architecture

This document explains the feature-based architecture implemented in the MCP Weather service.

## Overview

The feature-based architecture organizes code by features rather than by technical layers.
Each feature has its own models, routes, and tool implementations in a self-contained directory.

## Advantages

- **Cohesion**: Related code is kept together
- **Isolation**: Features are isolated from each other, reducing dependencies
- **Maintainability**: Easier to understand and maintain each feature
- **Scalability**: Makes it easier to add new features without modifying existing code
- **Testability**: Features can be tested in isolation

## Directory Structure

```
mcp_weather/
├── features/                 # Feature modules
│   ├── __init__.py          # Exports all features
│   └── hourly_weather/      # Hourly weather feature
│       ├── __init__.py      # Feature exports
│       ├── models.py        # Feature-specific models
│       ├── routes.py        # Feature REST endpoints
│       └── tool.py          # Feature MCP tools
├── shared/                  # Shared components
│   ├── __init__.py
│   └── models.py            # Shared models
└── ...                      # Other modules
```

## Components

### Features

Each feature should have at least:

1. **models.py** - Feature-specific data models
2. **routes.py** - REST API endpoints
3. **tool.py** - MCP tool implementation

### Shared Components

Common code used across features is placed in the `shared` directory:

1. **models.py** - Common data models (errors, base classes, etc.)
2. **utils.py** - Utility functions (future addition)

## Adding a New Feature

To add a new feature:

1. Create a new directory in `features/`
2. Add the required components (models, routes, tool)
3. Register the feature in `features/__init__.py`
4. Update `server.py` to include the new feature

## Integration

The `server.py` file automatically discovers and integrates all features:
- MCP tools are registered in the `register_mcp_tools` method
- REST endpoints are registered in the `create_router` method

## Future Enhancements

- Common middleware for features
- Feature-specific configuration
- Feature testing framework