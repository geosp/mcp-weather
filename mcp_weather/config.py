"""
Configuration management for Weather MCP Server

Handles environment variables and provides typed configuration objects.
All configuration is loaded from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class AuthentikConfig(BaseModel):
    """
    Authentik authentication configuration
    
    Required for HTTP transport mode to validate Bearer tokens.
    Not needed for stdio mode.
    """
    api_url: str = Field(..., description="Authentik API URL (e.g., http://authentik.example.com/api/v3)")
    api_token: str = Field(..., description="Authentik API token for authentication")
    
    @classmethod
    def from_env(cls) -> "AuthentikConfig":
        """Load Authentik configuration from environment variables"""
        api_url = os.getenv("AUTHENTIK_API_URL")
        api_token = os.getenv("AUTHENTIK_API_TOKEN")
        
        if not api_url or not api_token:
            raise ValueError(
                "AUTHENTIK_API_URL and AUTHENTIK_API_TOKEN environment variables must be set for HTTP mode"
            )
        
        return cls(api_url=api_url, api_token=api_token)
    
    @classmethod
    def from_env_optional(cls) -> Optional["AuthentikConfig"]:
        """Load Authentik config if available, return None if not configured"""
        try:
            return cls.from_env()
        except ValueError:
            return None


class CacheConfig(BaseModel):
    """
    Location cache configuration
    
    Caches geocoded location coordinates to reduce API calls.
    Uses JSON file storage in user's cache directory.
    """
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".cache" / "weather",
        description="Directory for cache files"
    )
    expiry_days: int = Field(
        default=30, 
        ge=1, 
        le=365,
        description="Number of days before cached location data expires"
    )
    
    @property
    def location_cache_file(self) -> Path:
        """Path to the location cache JSON file"""
        return self.cache_dir / "location_cache.json"
    
    @classmethod
    def from_env(cls) -> "CacheConfig":
        """Load cache configuration from environment variables"""
        cache_dir = os.getenv("CACHE_DIR")
        expiry_days = os.getenv("CACHE_EXPIRY_DAYS")
        
        kwargs = {}
        if cache_dir:
            kwargs["cache_dir"] = Path(cache_dir)
        if expiry_days:
            kwargs["expiry_days"] = int(expiry_days)
        
        return cls(**kwargs)


class ServerConfig(BaseModel):
    """
    HTTP server configuration
    
    Controls how the server listens for connections when using HTTP transport.
    """
    transport: Literal["stdio", "http"] = Field(
        default="stdio",
        description="Transport mode: 'stdio' for direct MCP, 'http' for web server"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Bind address (0.0.0.0 = all interfaces)"
    )
    port: int = Field(
        default=3000,
        ge=1,
        le=65535,
        description="Port number for HTTP server"
    )
    mcp_only: bool = Field(
        default=False,
        description="If True, serve pure MCP protocol; if False, serve REST + MCP"
    )
    
    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is a valid format"""
        if not v or v.strip() == "":
            raise ValueError("Host cannot be empty")
        return v.strip()
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load server configuration from environment variables"""
        transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "3000"))
        mcp_only = os.getenv("MCP_ONLY", "false").lower() == "true"
        
        return cls(
            transport=transport,
            host=host,
            port=port,
            mcp_only=mcp_only
        )


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
    weather_api: WeatherAPIConfig
    authentik: Optional[AuthentikConfig] = None
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load complete configuration from environment variables"""
        server = ServerConfig.from_env()
        cache = CacheConfig.from_env()
        weather_api = WeatherAPIConfig.from_env()
        
        # Only load Authentik config if using HTTP transport
        authentik = None
        if server.transport == "http":
            authentik = AuthentikConfig.from_env()
        
        return cls(
            server=server,
            cache=cache,
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