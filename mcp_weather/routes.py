"""
FastAPI routes for Weather MCP Server

Defines HTTP REST endpoints for weather data access.
All protected routes require Authentik Bearer token authentication.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

# Import your existing auth dependency
from core.auth_rest import get_token_from_header

from .weather_service import WeatherService
from .models import (
    WeatherResponse,
    WeatherRequest,
    HealthResponse,
    ServiceInfo,
    ErrorResponse,
)

logger = logging.getLogger(__name__)


def create_router(weather_service: WeatherService) -> APIRouter:
    """
    Create and configure FastAPI router with weather endpoints
    
    Args:
        weather_service: WeatherService instance for handling requests
        
    Returns:
        Configured APIRouter with all weather endpoints
    """
    router = APIRouter(
        prefix="",
        tags=["weather"],
        responses={
            401: {
                "description": "Unauthorized - Invalid or missing Bearer token",
                "model": ErrorResponse
            },
            503: {
                "description": "Service Unavailable - External API error",
                "model": ErrorResponse
            }
        }
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
        
        Use Cases:
            - Kubernetes liveness/readiness probes
            - Load balancer health checks
            - Service monitoring dashboards
        """
        return HealthResponse(
            status="healthy",
            service="mcp-weather",
            api="Open-Meteo",
            authentication="Authentik enabled",
            timestamp=datetime.utcnow()
        )
    
    # ========================================================================
    # Protected Endpoints (Require Authentication)
    # ========================================================================
    
    @router.get(
        "/weather",
        summary="Get Weather Data",
        description="Get current weather and hourly forecast for a location",
        response_model=WeatherResponse,
        responses={
            200: {
                "description": "Weather data retrieved successfully",
                "model": WeatherResponse
            },
            400: {
                "description": "Bad Request - Invalid location",
                "model": ErrorResponse
            },
            404: {
                "description": "Not Found - Location not found",
                "model": ErrorResponse
            }
        }
    )
    async def get_weather(
        location: str = Query(
            ...,
            description="City name or location (e.g., 'Tallahassee', 'London', 'Paris, France')",
            min_length=1,
            max_length=100,
            example="Tallahassee"
        ),
        user: Dict[str, Any] = Depends(get_token_from_header)
    ) -> WeatherResponse:
        """
        Get weather data for a location via HTTP GET
        
        This endpoint provides current weather conditions and a 12-hour forecast
        for any worldwide location. It requires Authentik Bearer token authentication.
        
        Authentication:
            Requires valid Bearer token in Authorization header.
            Token is validated via your existing core.auth infrastructure.
        
        Query Parameters:
            - location: City name (required)
                - Can be just city name: "London"
                - Or city with country: "Paris, France"
                - Case insensitive
        
        Response:
            Returns comprehensive weather data including:
            - Location information (name, country, coordinates, timezone)
            - Current conditions (temperature, humidity, wind, precipitation)
            - 12-hour hourly forecast
            - Weather descriptions in plain English
            - Data source attribution
        
        Example Request:
            GET /weather?location=Tallahassee
            Authorization: Bearer <your-token>
        
        Example Response:
            {
                "location": "Tallahassee",
                "country": "United States",
                "coordinates": {"latitude": 30.4383, "longitude": -84.2807},
                "timezone": "America/New_York",
                "current_conditions": {
                    "temperature": {"value": 22.5, "unit": "°C"},
                    "weather": "Partly cloudy",
                    ...
                },
                "hourly_forecast": [...],
                "data_source": "Open-Meteo API (https://open-meteo.com)"
            }
        
        Errors:
            - 400: Invalid location format or empty location
            - 401: Missing or invalid Bearer token
            - 404: Location not found in geocoding database
            - 503: Weather service or geocoding API unavailable
        """
        try:
            # Log authenticated user for audit trail
            username = user.get("username", "unknown")
            logger.info(
                f"Weather request from user '{username}' for location '{location}'"
            )
            
            # Fetch weather data
            weather_data = await weather_service.get_weather(location)
            
            logger.info(
                f"Weather request successful: {location} -> "
                f"{weather_data.current_conditions.temperature.value}°C"
            )
            
            return weather_data
            
        except ValueError as e:
            # Invalid location format
            logger.warning(f"Invalid location from user '{username}': {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except HTTPException:
            # Re-raise HTTP exceptions (404, 503, etc.)
            raise
        except Exception as e:
            # Unexpected error
            logger.error(
                f"Unexpected error in get_weather for '{location}': {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    @router.post(
        "/weather",
        summary="Get Weather Data (POST)",
        description="Get weather data using POST request with JSON body",
        response_model=WeatherResponse,
        responses={
            200: {
                "description": "Weather data retrieved successfully",
                "model": WeatherResponse
            },
            400: {
                "description": "Bad Request - Invalid request body",
                "model": ErrorResponse
            },
            404: {
                "description": "Not Found - Location not found",
                "model": ErrorResponse
            }
        }
    )
    async def post_weather(
        request: WeatherRequest,
        user: Dict[str, Any] = Depends(get_token_from_header)
    ) -> WeatherResponse:
        """
        Get weather data for a location via HTTP POST
        
        Alternative endpoint using POST with JSON body instead of query parameters.
        Useful for programmatic access or when location names contain special characters.
        
        Authentication:
            Requires valid Bearer token in Authorization header.
        
        Request Body:
            {
                "location": "Tallahassee"
            }
        
        Response:
            Same as GET /weather endpoint
        
        Example Request:
            POST /weather
            Authorization: Bearer <your-token>
            Content-Type: application/json
            
            {
                "location": "New York"
            }
        """
        try:
            username = user.get("username", "unknown")
            logger.info(
                f"Weather POST request from user '{username}' for location '{request.location}'"
            )
            
            weather_data = await weather_service.get_weather(request.location)
            
            logger.info(
                f"Weather POST request successful: {request.location} -> "
                f"{weather_data.current_conditions.temperature.value}°C"
            )
            
            return weather_data
            
        except ValueError as e:
            logger.warning(f"Invalid location from user '{username}': {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in post_weather for '{request.location}': {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    # Error handlers moved to server.py FastAPI app
    
    logger.info("Weather routes registered successfully")
    return router


def get_route_descriptions() -> Dict[str, str]:
    """
    Get descriptions of all available routes
    
    Useful for generating documentation or admin interfaces.
    
    Returns:
        Dict mapping route paths to their descriptions
    """
    return {
        "/": "Service information and available endpoints",
        "/health": "Health check endpoint (no auth)",
        "/weather (GET)": "Get weather data via query parameter (auth required)",
        "/weather (POST)": "Get weather data via JSON body (auth required)"
    }