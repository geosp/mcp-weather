"""
Core configuration for shared infrastructure

Provides base configuration classes and utilities that can be reused across
multiple projects. Handles common configuration concerns like authentication,
caching strategies, and environment variable loading.
"""

import os
from pathlib import Path
from typing import Optional, TypeVar, Type, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

T = TypeVar('T', bound=BaseModel)


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


class BaseCacheConfig(BaseModel):
    """
    Base configuration for caching mechanisms
    
    Provides common cache settings that can be extended for specific use cases.
    """
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".cache",
        description="Base directory for cache files"
    )
    expiry_days: int = Field(
        default=30, 
        ge=1, 
        le=365,
        description="Number of days before cached data expires"
    )
    
    @classmethod
    def from_env(cls: Type[T], env_prefix: str = "") -> T:
        """
        Load cache configuration from environment variables
        
        Args:
            env_prefix: Optional prefix for environment variables
            
        Returns:
            Configured cache instance
        """
        cache_dir = os.getenv(f"{env_prefix}CACHE_DIR")
        expiry_days = os.getenv(f"{env_prefix}CACHE_EXPIRY_DAYS")
        
        kwargs: Dict[str, Any] = {}
        if cache_dir:
            kwargs["cache_dir"] = Path(cache_dir)
        if expiry_days:
            kwargs["expiry_days"] = int(expiry_days)
        
        return cls(**kwargs)


class BaseServerConfig(BaseModel):
    """
    Base HTTP server configuration
    
    Controls how servers listen for connections when using HTTP transport.
    Can be extended for specific server implementations.
    """
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
    
    @classmethod
    def from_env(cls: Type[T], env_prefix: str = "") -> T:
        """
        Load server configuration from environment variables
        
        Args:
            env_prefix: Optional prefix for environment variables
            
        Returns:
            Configured server instance
        """
        host = os.getenv(f"{env_prefix}HOST", "0.0.0.0")
        port_str = os.getenv(f"{env_prefix}PORT", "3000")
        
        try:
            port = int(port_str)
        except ValueError:
            port = 3000
            
        kwargs: Dict[str, Any] = {
            "host": host,
            "port": port
        }
        
        return cls(**kwargs)