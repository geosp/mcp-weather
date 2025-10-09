"""
Configuration management for Weather MCP Server

Handles environment variables and provides typed configuration objects
specific to the weather service. Extends core configuration classes.
"""

import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from core.config import (
    AuthentikConfig,
    BaseCacheConfig,
    BaseServerConfig,
    RedisCacheConfig,
    load_dotenv
)

# Ensure environment variables are loaded
load_dotenv()


class CacheConfig(BaseCacheConfig):
    """
    Location cache configuration
    
    Caches geocoded location coordinates to reduce API calls.
    Uses JSON file storage in user's cache directory.
    """
    def __init__(self, **data):
        super().__init__(**data)
        # Override cache_dir with weather-specific subfolder
        if "cache_dir" not in data:
            self.cache_dir = Path.home() / ".cache" / "weather"
    
    @property
    def location_cache_file(self) -> Path:
        """Path to the location cache JSON file"""
        return self.cache_dir / "location_cache.json"
    
    @classmethod
    def from_env(cls) -> "CacheConfig":
        """Load weather-specific cache configuration from environment variables"""
        return super().from_env(env_prefix="WEATHER_")


class ServerConfig(BaseServerConfig):
    """
    Weather MCP server configuration
    
    Controls how the server listens for connections and operational mode.
    """
    transport: Literal["stdio", "http"] = Field(
        default="stdio",
        description="Transport mode: 'stdio' for direct MCP, 'http' for web server"
    )
    mcp_only: bool = Field(
        default=False,
        description="If True, serve pure MCP protocol; if False, serve REST + MCP"
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="List of allowed origins for CORS"
    )
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load weather server configuration from environment variables"""
        config = super().from_env(env_prefix="MCP_")
        
        transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
        mcp_only = os.getenv("MCP_ONLY", "false").lower() == "true"
        
        # Parse CORS origins from environment
        cors_origins_str = os.getenv("MCP_CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        
        config.transport = transport
        config.mcp_only = mcp_only
        config.cors_origins = cors_origins
        
        return config


class WeatherAPIConfig(BaseModel):
    """
    Open-Meteo API configuration
    
    URLs for geocoding and weather data endpoints.
    No API key required for Open-Meteo.
    """
    geocoding_url: str = Field(
        default="https://geocoding-api.open-meteo.com/v1/search",
        description="Open-Meteo Geocoding API endpoint"
    )
    weather_url: str = Field(
        default="https://api.open-meteo.com/v1/forecast",
        description="Open-Meteo Weather API endpoint"
    )
    
    @classmethod
    def from_env(cls) -> "WeatherAPIConfig":
        """Load weather API configuration from environment variables"""
        geocoding_url = os.getenv("WEATHER_GEOCODING_URL")
        weather_url = os.getenv("WEATHER_API_URL")
        
        kwargs = {}
        if geocoding_url:
            kwargs["geocoding_url"] = geocoding_url
        if weather_url:
            kwargs["weather_url"] = weather_url
        
        return cls(**kwargs)


class AppConfig(BaseModel):
    """
    Complete application configuration
    
    Aggregates all configuration sections into a single object.
    """
    server: ServerConfig
    cache: CacheConfig
    redis_cache: RedisCacheConfig
    weather_api: WeatherAPIConfig
    authentik: Optional[AuthentikConfig] = None
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load complete configuration from environment variables"""
        server = ServerConfig.from_env()
        cache = CacheConfig.from_env()
        redis_cache = RedisCacheConfig.from_env(env_prefix="MCP_")
        weather_api = WeatherAPIConfig.from_env()
        
        # Only load Authentik config if using HTTP transport
        authentik = None
        if server.transport == "http":
            authentik = AuthentikConfig.from_env_optional()
        
        return cls(
            server=server,
            cache=cache,
            redis_cache=redis_cache,
            weather_api=weather_api,
            authentik=authentik
        )
    
    def validate_for_transport(self) -> None:
        """
        Validate configuration is complete for the selected transport mode
        
        Raises:
            ValueError: If required configuration is missing for the transport mode
        """
        if self.server.transport == "http" and self.authentik is None:
            raise ValueError(
                "Authentik configuration required for HTTP transport mode. "
                "Set AUTHENTIK_API_URL and AUTHENTIK_API_TOKEN environment variables."
            )


# Global configuration instance (loaded lazily)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get global application configuration
    
    Loads configuration on first access and caches it.
    Call load_config() explicitly if you need to reload.
    
    Returns:
        AppConfig: Complete application configuration
    """
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def load_config(validate: bool = True) -> AppConfig:
    """
    Load application configuration from environment
    
    Args:
        validate: If True, validate configuration for transport mode
        
    Returns:
        AppConfig: Complete application configuration
        
    Raises:
        ValueError: If configuration is invalid or incomplete
    """
    global _config
    _config = AppConfig.from_env()
    
    if validate:
        _config.validate_for_transport()
    
    return _config