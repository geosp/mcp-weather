"""
Main server module for Weather MCP Server

Handles application initialization, configuration, and server startup.
Supports both MCP-only mode and REST+MCP hybrid mode.
"""

import os
import logging
import sys
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
import uvicorn

from .config import get_config, load_config, AppConfig
from .cache import LocationCache
from .weather_service import WeatherService
try:
    from core.auth_provider import create_auth_provider
    CORE_AUTH_AVAILABLE = True
except ImportError:
    CORE_AUTH_AVAILABLE = False
    create_auth_provider = None
from .routes import create_router
from .tools import register_tools

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
# Application Factory
# ============================================================================

def create_weather_service(config: AppConfig) -> WeatherService:
    """
    Create and configure WeatherService instance
    
    Args:
        config: Application configuration
        
    Returns:
        Configured WeatherService instance
    """
    cache = LocationCache(config.cache)
    weather_service = WeatherService(config.weather_api, cache)
    
    logger.info("WeatherService initialized")
    return weather_service


def create_mcp_app(config: AppConfig) -> FastMCP:
    """
    Create FastMCP application with weather tools
    
    Args:
        config: Application configuration
        
    Returns:
        Configured FastMCP application
    """
    # Initialize authentication if using HTTP transport
    auth_provider = None
    if config.server.transport == "http" and config.authentik:
        if CORE_AUTH_AVAILABLE:
            try:
                # Create a service-specific auth provider for weather
                auth_provider = create_auth_provider("weather")
                logger.info("MCP authentication enabled using core auth provider")
            except Exception as e:
                logger.warning(f"Failed to create auth provider: {e}")
                logger.error(f"Authentication initialization failed: {e}")
        else:
            logger.error("Core auth provider not available - authentication disabled")
            logger.error("Please ensure core.auth_provider is accessible")
    
    # Create MCP server
    mcp = FastMCP(
        "mcp-weather",
        auth=auth_provider
    )
    
    # Create weather service
    weather_service = create_weather_service(config)
    
    # Register MCP tools
    register_tools(mcp, weather_service)
    
    logger.info("FastMCP application created")
    return mcp


def create_fastapi_app(config: AppConfig, mcp: FastMCP) -> FastAPI:
    """
    Create FastAPI application with MCP mounted and REST routes
    
    Args:
        config: Application configuration
        mcp: FastMCP application to mount
        
    Returns:
        Configured FastAPI application
    """
    # Get MCP ASGI app
    mcp_app = mcp.http_app()
    
    # Create FastAPI app
    app = FastAPI(
        title="Weather MCP Server",
        description=(
            "Authenticated MCP server for weather data using Open-Meteo API and Authentik. "
            "Provides both MCP protocol access and REST API endpoints."
        ),
        version="2.0.0",
        lifespan=mcp_app.lifespan,  # Critical: Use MCP's lifespan for proper session management
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8080",
            "https://agentgateway.mixwarecs-home.net",
            "http://agentgateway.mixwarecs-home.net",
            "*"  # TODO: Restrict in production
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Create weather service for REST routes
    weather_service = create_weather_service(config)
    
    # Create and include REST routes
    router = create_router(weather_service)
    app.include_router(router)
    
    # Mount MCP server at /mcp
    app.mount("/mcp", mcp_app)
    
    # Add exception handlers to the main app
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    from datetime import datetime
    from .models import ErrorResponse, ErrorDetail
    
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
    
    logger.info("FastAPI application created with MCP mounted at /mcp")
    return app


# ============================================================================
# Server Startup
# ============================================================================

def validate_configuration(config: AppConfig) -> None:
    """
    Validate configuration and log startup information
    
    Args:
        config: Application configuration to validate
        
    Raises:
        SystemExit: If configuration is invalid
    """
    try:
        config.validate_for_transport()
        
        logger.info("=" * 70)
        logger.info("Weather MCP Server - Configuration")
        logger.info("=" * 70)
        logger.info(f"Transport: {config.server.transport}")
        logger.info(f"MCP Only: {config.server.mcp_only}")
        
        if config.server.transport == "http":
            logger.info(f"Host: {config.server.host}")
            logger.info(f"Port: {config.server.port}")
            
            if config.authentik:
                logger.info(f"Authentication: Authentik ({config.authentik.api_url})")
            else:
                logger.warning("Authentication: DISABLED (stdio mode)")
        else:
            logger.info("Mode: stdio (no authentication)")
        
        logger.info(f"Weather API: {config.weather_api.weather_url}")
        logger.info(f"Geocoding API: {config.weather_api.geocoding_url}")
        logger.info(f"Cache Directory: {config.cache.cache_dir}")
        logger.info(f"Cache Expiry: {config.cache.expiry_days} days")
        logger.info("=" * 70)
        
    except ValueError as e:
        logger.error("=" * 70)
        logger.error("CONFIGURATION ERROR")
        logger.error("=" * 70)
        logger.error(str(e))
        logger.error("=" * 70)
        sys.exit(1)


def run_mcp_only(config: AppConfig) -> None:
    """
    Run pure MCP server (MCP protocol only, no REST endpoints)
    
    Args:
        config: Application configuration
    """
    logger.info("Starting Weather MCP Server in MCP-only mode")
    logger.info("=" * 70)
    
    if config.server.transport == "http":
        logger.info(f"MCP endpoint: http://{config.server.host}:{config.server.port}/")
        logger.info("Note: All MCP requests require Bearer token authentication")
    else:
        logger.info("MCP endpoint: stdio")
        logger.info("Note: stdio mode does not require authentication")
    
    logger.info("=" * 70)
    
    # Create MCP app
    mcp = create_mcp_app(config)
    
    # Run MCP server
    if config.server.transport == "http":
        mcp.run(
            transport="http",
            host=config.server.host,
            port=config.server.port
        )
    else:
        mcp.run(transport="stdio")


def run_rest_and_mcp(config: AppConfig) -> None:
    """
    Run FastAPI + MCP server (REST endpoints + MCP protocol)
    
    Args:
        config: Application configuration
    """
    logger.info("Starting Weather MCP Server with REST API + MCP")
    logger.info("=" * 70)
    logger.info(f"Server: http://{config.server.host}:{config.server.port}")
    logger.info(f"API Docs: http://{config.server.host}:{config.server.port}/docs")
    logger.info(f"Health Check: http://{config.server.host}:{config.server.port}/health")
    logger.info(f"MCP Endpoint: http://{config.server.host}:{config.server.port}/mcp")
    logger.info("")
    logger.info("Available REST Endpoints:")
    logger.info("  GET  / - Service information")
    logger.info("  GET  /health - Health check (no auth)")
    logger.info("  GET  /weather?location=<city> - Get weather (auth required)")
    logger.info("  POST /weather - Get weather via JSON body (auth required)")
    logger.info("")
    logger.info("Note: All endpoints except /health require Bearer token authentication")
    logger.info("=" * 70)
    
    # Create MCP app
    mcp = create_mcp_app(config)
    
    # Create FastAPI app with MCP mounted
    app = create_fastapi_app(config, mcp)
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        log_level="info"
    )


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
    
    Startup Modes:
        1. stdio mode: Pure MCP protocol over stdin/stdout (no auth)
           MCP_TRANSPORT=stdio python -m mcp_weather.server
        
        2. HTTP MCP-only: Pure MCP protocol over HTTP (with auth)
           MCP_TRANSPORT=http MCP_ONLY=true python -m mcp_weather.server
        
        3. HTTP REST+MCP: Both REST API and MCP protocol (with auth)
           MCP_TRANSPORT=http MCP_ONLY=false python -m mcp_weather.server
    
    Exit Codes:
        0: Normal exit
        1: Configuration error or startup failure
    """
    try:
        # Load and validate configuration
        config = load_config(validate=True)
        validate_configuration(config)
        
        # Start server based on configuration
        if config.server.transport == "stdio":
            # stdio mode - pure MCP protocol
            run_mcp_only(config)
        elif config.server.mcp_only:
            # HTTP mode - pure MCP protocol
            run_mcp_only(config)
        else:
            # HTTP mode - REST API + MCP protocol
            run_rest_and_mcp(config)
            
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
    mcp = create_mcp_app(config)
    app = create_fastapi_app(config, mcp)
    return app


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "main",
    "create_app",
    "create_mcp_app",
    "create_fastapi_app",
    "create_weather_service"
]


# ============================================================================
# Script Entry Point
# ============================================================================

if __name__ == "__main__":
    main()