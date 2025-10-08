"""
Weather MCP server implementation using the reusable base server

This module implements a weather-specific server based on the reusable
base server components in core.server.

Uses a feature-based architecture where each feature has its own
models, routes, and tool implementations.
"""

import logging
import sys
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastmcp import FastMCP

from core.server import BaseMCPServer, BaseService
from mcp_weather.config import load_config, AppConfig
from mcp_weather.cache import LocationCache
from mcp_weather.weather_service import WeatherService
from mcp_weather.shared.models import ErrorResponse, ErrorDetail

# Import features
from mcp_weather.features import hourly_weather

try:
    from core.auth_mcp import create_auth_provider, get_auth_provider
    CORE_AUTH_AVAILABLE = True
except ImportError:
    CORE_AUTH_AVAILABLE = False
    create_auth_provider = None
    get_auth_provider = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Weather Service Implementation
# ============================================================================

class WeatherMCPService(BaseService):
    """
    Weather service implementation for MCP
    
    This service provides weather forecast functionality via
    Open-Meteo API with location caching.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the weather service
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.weather_service = None
    
    def initialize(self) -> None:
        """Initialize the weather service and its dependencies"""
        # Create the location cache and weather service directly
        location_cache = LocationCache(self.config.cache)
        self.weather_service = WeatherService(self.config.weather_api, location_cache)
        logger.info("WeatherMCPService initialized with enhanced location handling")
    
    def get_service_name(self) -> str:
        """Get the name of this service"""
        return "mcp-weather"
    
    def register_mcp_tools(self, mcp: FastMCP) -> None:
        """Register MCP tools for the weather service"""
        if self.weather_service is None:
            raise ValueError("Weather service not initialized")
        
        # Register tools from feature modules
        hourly_weather.tool.register_tool(mcp, self.weather_service)
        
        logger.info("Registered weather tools with MCP server")


# ============================================================================
# Weather MCP Server Implementation
# ============================================================================

class WeatherMCPServer(BaseMCPServer):
    """
    Weather-specific MCP server implementation
    
    Extends the base MCP server with weather-specific functionality.
    """
    
    @property
    def service_title(self) -> str:
        """Get the title for this MCP service"""
        return "Weather MCP Server"
    
    @property
    def service_description(self) -> str:
        """Get the description for this MCP service"""
        return (
            "Authenticated MCP server for weather data using Open-Meteo API and Authentik. "
            "Provides both MCP protocol access and REST API endpoints."
        )
    
    @property
    def service_version(self) -> str:
        """Get the version string for this MCP service"""
        return "2.0.0"
    
    @property
    def allowed_cors_origins(self) -> List[str]:
        """Get list of allowed origins for CORS"""
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://agentgateway.mixwarecs-home.net",
            "http://agentgateway.mixwarecs-home.net",
            "*"  # TODO: Restrict in production
        ]
    
    def create_auth_provider(self) -> Optional[Any]:
        """
        Create an authentication provider for this server
        
        Returns:
            Authentication provider or None if not using authentication
        """
        auth_provider = None
        config = self.config
        
        if hasattr(config, "authentik") and config.authentik:
            if CORE_AUTH_AVAILABLE:
                try:
                    # Get or create a service-specific auth provider for weather using singleton pattern
                    auth_provider = get_auth_provider("weather")
                    logger.info("MCP authentication enabled using core auth provider (singleton)")
                except Exception as e:
                    logger.warning(f"Failed to create auth provider: {e}")
                    logger.error(f"Authentication initialization failed: {e}")
            else:
                logger.error("Core auth provider not available - authentication disabled")
                logger.error("Please ensure core.auth_provider is accessible")
        
        return auth_provider
    
    def create_router(self) -> APIRouter:
        """
        Create a FastAPI router for REST endpoints
        
        Returns:
            Router with REST API endpoints
        """
        # Create a new instance of WeatherService for REST routes
        # to avoid potential concurrency issues with the MCP service
        weather_service_config = AppConfig.from_env()
        location_cache = LocationCache(weather_service_config.cache)
        weather_service = WeatherService(
            weather_service_config.weather_api,
            location_cache
        )
        
        # Create main router with no prefix
        main_router = APIRouter()
        
        # Create and mount feature routers
        hourly_weather_router = hourly_weather.routes.create_router(
            weather_service
        )
        main_router.include_router(hourly_weather_router)
        
        # Add root and health endpoints
        from mcp_weather.routes import create_base_router
        base_router = create_base_router()
        main_router.include_router(base_router)
        
        return main_router
    
    def register_exception_handlers(self, app: FastAPI) -> None:
        """
        Register exception handlers for the FastAPI application
        
        Args:
            app: FastAPI application to register handlers with
        """
        @app.exception_handler(HTTPException)
        async def app_http_exception_handler(request, exc):
            """Handle HTTP exceptions with custom format"""
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(
                    success=False,
                    error=ErrorDetail(
                        message=exc.detail,
                        error_code=f"HTTP_{exc.status_code}"
                    ),
                    timestamp=datetime.utcnow()
                ).model_dump()
            )
        
        @app.exception_handler(RequestValidationError)
        async def app_validation_exception_handler(request, exc):
            """Handle validation errors with custom format"""
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    success=False,
                    error=ErrorDetail(
                        message="Validation error",
                        error_code="VALIDATION_ERROR",
                        details=exc.errors()
                    ),
                    timestamp=datetime.utcnow()
                ).model_dump()
            )
    
    def validate_configuration(self) -> None:
        """
        Validate server configuration
        
        Raises:
            ValueError: If configuration is invalid
        """
        config = self.config
        
        try:
            # Validate core configuration
            if hasattr(config, "validate_for_transport"):
                config.validate_for_transport()
            
            # Log configuration information
            logger.info("=" * 70)
            logger.info("Weather MCP Server - Configuration")
            logger.info("=" * 70)
            
            if hasattr(config, "server"):
                logger.info(f"Transport: {config.server.transport}")
                logger.info(f"MCP Only: {config.server.mcp_only}")
                
                if config.server.transport == "http":
                    logger.info(f"Host: {config.server.host}")
                    logger.info(f"Port: {config.server.port}")
                    
                    if hasattr(config, "authentik") and config.authentik:
                        logger.info(f"Authentication: Authentik ({config.authentik.api_url})")
                    else:
                        logger.warning("Authentication: DISABLED (stdio mode)")
                else:
                    logger.info("Mode: stdio (no authentication)")
            
            if hasattr(config, "weather_api"):
                logger.info(f"Weather API: {config.weather_api.weather_url}")
                logger.info(f"Geocoding API: {config.weather_api.geocoding_url}")
            
            if hasattr(config, "cache"):
                logger.info(f"Cache Directory: {config.cache.cache_dir}")
                logger.info(f"Cache Expiry: {config.cache.expiry_days} days")
            
            logger.info("=" * 70)
            
        except ValueError as e:
            logger.error("=" * 70)
            logger.error("CONFIGURATION ERROR")
            logger.error("=" * 70)
            logger.error(str(e))
            logger.error("=" * 70)
            raise


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> None:
    """
    Main entry point for the Weather MCP Server
    
    Handles configuration loading, validation, and server startup.
    Supports both stdio and HTTP transport modes with optional REST API.
    
    Environment Variables:
        MCP_TRANSPORT: "stdio" or "http" (default: "stdio")
        MCP_HOST: Bind address for HTTP mode (default: "0.0.0.0")
        MCP_PORT: Port for HTTP mode (default: "3000")
        MCP_ONLY: "true" for pure MCP, "false" for REST+MCP (default: "false")
        AUTHENTIK_API_URL: Authentik API URL (required for HTTP mode)
        AUTHENTIK_API_TOKEN: Authentik API token (required for HTTP mode)
        CACHE_DIR: Cache directory path (default: ~/.cache/weather)
        CACHE_EXPIRY_DAYS: Cache expiry in days (default: 30)
    """
    try:
        # Load configuration
        config = load_config(validate=True)
        
        # Create service
        service = WeatherMCPService(config)
        
        # Create server
        server = WeatherMCPServer(config, service)
        
        # Run server
        server.run()
            
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(1)


# ============================================================================
# Application Factory for External Use
# ============================================================================

def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application
    
    This is useful for deployment with ASGI servers like gunicorn:
        gunicorn mcp_weather.server:create_app --worker-class uvicorn.workers.UvicornWorker
    
    Returns:
        Configured FastAPI application with MCP mounted
    """
    config = load_config(validate=True)
    service = WeatherMCPService(config)
    server = WeatherMCPServer(config, service)
    
    return server.create_app()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "main",
    "create_app",
    "WeatherMCPService",
    "WeatherMCPServer"
]


# ============================================================================
# Script Entry Point
# ============================================================================

if __name__ == "__main__":
    main()