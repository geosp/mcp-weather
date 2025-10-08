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

from mcp_weather.server import (
    main,
    create_app,
    WeatherMCPService,
    WeatherMCPServer
)
from mcp_weather.config import (
    get_config,
    load_config,
    AppConfig,
    ServerConfig,
    CacheConfig,
    WeatherAPIConfig,
    AuthentikConfig
)
from mcp_weather.weather_service import WeatherService
from mcp_weather.models import LocationData
from core.cache import RedisCacheClient
# Import authentication components directly from core
from core.auth_mcp import (
    AuthentikAuthProvider,
    AuthInfo
)

__version__ = "2.0.0"
__author__ = "Geovanny Fajardo"

__all__ = [
    # Server functions
    "main",
    "create_app",
    "WeatherMCPService",
    "WeatherMCPServer",
    
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
    "RedisCacheClient",
    "LocationData",
    
    # Authentication
    "AuthentikAuthProvider",
    "AuthInfo",
    
    # Metadata
    "__version__",
    "__author__"
]