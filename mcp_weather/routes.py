"""
Base routes for the Weather MCP Server

Defines root and health HTTP endpoints.
These endpoints don't require authentication.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .shared.models import HealthResponse, ServiceInfo

logger = logging.getLogger(__name__)


def create_base_router() -> APIRouter:
    """
    Create and configure FastAPI router with base endpoints
    
    Returns:
        Configured APIRouter with root and health endpoints
    """
    router = APIRouter(
        prefix="",
        tags=["base"],
    )
    
    # ========================================================================
    # Public Endpoints (No Authentication)
    # ========================================================================
    
    @router.get(
        "/",
        summary="Service Information",
        description="Get information about the Weather MCP Server",
        response_model=ServiceInfo
    )
    async def root() -> ServiceInfo:
        """
        Root endpoint with service information
        
        Returns basic information about the service, available endpoints,
        and authentication requirements.
        
        No authentication required.
        """
        return ServiceInfo(
            name="Weather MCP Server",
            version="2.0.0",
            authentication="Authentik Bearer token required",
            api="Open-Meteo (https://open-meteo.com)",
            note="No API key required for weather data!",
            endpoints={
                "health": "/health (no auth)",
                "weather": "/weather?location=<city> (auth required)",
                "docs": "/docs",
                "mcp": "/mcp (MCP protocol, auth required)"
            }
        )
    
    @router.get(
        "/health",
        summary="Health Check",
        description="Check if the service is running and healthy",
        response_model=HealthResponse,
        tags=["monitoring"]
    )
    async def health() -> HealthResponse:
        """
        Health check endpoint for monitoring and load balancers
        
        Returns the service health status. Always returns 200 OK if the
        service is running.
        
        No authentication required.
        """
        return HealthResponse(
            success=True,
            status="ok",
            message="Weather MCP server is running",
            version="2.0.0"
        )
    
    return router