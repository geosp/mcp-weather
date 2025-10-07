"""
Weather MCP Server Package

A secure, Authentik-authenticated MCP server providing weather data via Open-Meteo API.

Features:
    - FastMCP 2.0 integration for AI tool access
    - REST API endpoints for web applications
    - Authentik Bearer token authentication
    - Location caching for performance
    - Free Open-Meteo API (no API key required)
    - Support for stdio and HTTP transports

Usage:
    # Run as MCP server
    python -m mcp_weather.server
    
    # Or import and use programmatically
    from mcp_weather import create_app
    app = create_app()

Author: Weather MCP Team
Version: 2.0.0
License: MIT
"""

from .server import (
    main,
    create_app,
    create_mcp_app,
    create_fastapi_app,
    create_weather_service
)
from .config import (
    get_config,
    load_config,
    AppConfig,
    ServerConfig,
    CacheConfig,
    WeatherAPIConfig,
    AuthentikConfig
)
from .weather_service import WeatherService
from .cache import LocationCache, LocationData
from .auth_provider import (
    AuthentikAuthProvider,
    get_mcp_auth_provider,
    initialize_mcp_auth
)

__version__ = "2.0.0"
__author__ = "Geovanny Fajardo"

__all__ = [
    # Server functions
    "main",
    "create_app",
    "create_mcp_app",
    "create_fastapi_app",
    "create_weather_service",
    
    # Configuration
    "get_config",
    "load_config",
    "AppConfig",
    "ServerConfig",
    "CacheConfig",
    "WeatherAPIConfig",
    "AuthentikConfig",
    
    # Core services
    "WeatherService",
    "LocationCache",
    "LocationData",
    
    # Authentication
    "AuthentikAuthProvider",
    "get_mcp_auth_provider",
    "initialize_mcp_auth",
    
    # Metadata
    "__version__",
    "__author__"
]