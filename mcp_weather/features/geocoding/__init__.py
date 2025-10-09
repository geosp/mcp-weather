"""
Geocoding feature for the Weather MCP

Provides geocoding functionality to convert location names to coordinates and timezone information.
"""

from mcp_weather.features.geocoding.routes import create_router
from mcp_weather.features.geocoding.tool import register_tool

__all__ = ["create_router", "register_tool"]