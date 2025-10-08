"""
Features package for the MCP Weather service

This package organizes features into self-contained modules.
Each feature has its own models, routes, and tool implementations.
"""

from . import hourly_weather

__all__ = ["hourly_weather"]