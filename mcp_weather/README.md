# MCP Weather Service - Feature-Based Architecture

## Overview

The MCP Weather service has been restructured to use a feature-based architecture. This approach organizes the codebase by features rather than by technical layers, making it more maintainable and easier to extend.

## Architecture

The new architecture is organized as follows:

```
mcp_weather/
├── features/                 # Feature modules
│   ├── __init__.py          # Exports all features
│   ├── README.md            # Documentation for feature-based structure
│   └── hourly_weather/      # Hourly weather feature
│       ├── __init__.py      # Feature exports
│       ├── models.py        # Feature-specific models
│       ├── routes.py        # Feature REST endpoints
│       └── tool.py          # Feature MCP tools
├── shared/                  # Shared components
│   ├── __init__.py
│   ├── README.md            # Documentation for shared components
│   └── models.py            # Shared models
└── ...                      # Other modules
```

## Key Components

### Features

Each feature is self-contained with its own:
- Models: Feature-specific data structures
- Routes: REST API endpoints
- Tools: MCP tool implementations

### Enhanced Location Handling

The service includes built-in enhanced location handling capabilities:
- **City, Country format support**: Better handling of locations like "Paris, France" vs "Paris, Texas"
- **State/Province handling**: Support for formats like "Cleveland, GA" to distinguish from "Cleveland, OH"
- **Special character support**: Properly handles names with accents like "São Paulo" or "München"
- **Smart caching**: Prevents cache collisions between similarly named cities in different regions

This functionality is built into the core components:
- `LocationCache` now includes enhanced parsing for city, state, and country components
- `WeatherService` leverages this parsing for better geocoding results

### Shared Components

Common code used across features:
- Models: Base classes, error models, common data structures

## Benefits

- **Cohesion**: Related code is kept together
- **Isolation**: Features are isolated, reducing dependencies
- **Maintainability**: Easier to understand and maintain
- **Scalability**: Easier to add new features
- **Testability**: Features can be tested in isolation

## Adding New Features

To add a new feature:

1. Create a directory in `features/`
2. Add the required components (models, routes, tool)
3. Register the feature in `features/__init__.py`
4. Update server.py to include the new feature

## Implementation Notes

The server implementation automatically discovers and integrates all features:
- MCP tools are registered in the `register_mcp_tools` method
- REST endpoints are registered in the `create_router` method

## Future Enhancements

- Feature-specific configuration
- Feature testing framework
- Middleware components
- Additional weather features (daily forecasts, historical data, etc.)