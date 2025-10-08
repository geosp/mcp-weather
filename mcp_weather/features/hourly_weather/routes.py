"""
Hourly Weather Routes Module

Defines FastAPI endpoints for the hourly weather feature.
All protected routes require Authentik Bearer token authentication.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

# Import auth dependency
from core.auth_rest import get_token_from_header

from ...weather_service import WeatherService
from .models import WeatherResponse, WeatherRequest
from ...shared.models import ErrorResponse

logger = logging.getLogger(__name__)

def create_router(weather_service: WeatherService) -> APIRouter:
    """
    Create and configure FastAPI router with hourly weather endpoints
    
    Args:
        weather_service: WeatherService instance for handling requests
        
    Returns:
        Configured APIRouter with hourly weather endpoints
    """
    router = APIRouter(
        prefix="/weather",
        tags=["hourly-weather"],
        responses={
            401: {
                "description": "Unauthorized - Invalid or missing Bearer token",
                "model": ErrorResponse
            },
            404: {
                "description": "Not Found - Location could not be geocoded",
                "model": ErrorResponse
            },
            503: {
                "description": "Service Unavailable - External API error",
                "model": ErrorResponse
            }
        }
    )
    
    @router.get(
        "",
        summary="Get Weather Forecast",
        description="Get current conditions and hourly weather forecast for a location",
        response_model=WeatherResponse,
        responses={
            200: {
                "description": "Weather data retrieved successfully",
                "model": WeatherResponse
            },
            400: {
                "description": "Bad Request - Invalid location format",
                "model": ErrorResponse
            }
        }
    )
    async def get_weather(
        location: str = Query(
            ...,
            description="Location name (city or 'city, country')",
            min_length=1,
            max_length=100,
            examples=["London", "New York", "Tokyo", "Paris, France"],
        ),
        token: str = Depends(get_token_from_header)
    ) -> WeatherResponse:
        """
        Get weather forecast for the specified location
        
        Retrieves current weather conditions and hourly forecast for the next 12 hours.
        Location can be specified as city name or "city, country" format.
        
        Authentication required: Bearer token
        
        Args:
            location: Location name (city or "city, country")
            token: Authentik Bearer token (from Authorization header)
            
        Returns:
            Weather data including current conditions and hourly forecasts
            
        Raises:
            HTTPException 400: Invalid location format
            HTTPException 401: Invalid or missing authentication
            HTTPException 404: Location not found
            HTTPException 503: Weather service unavailable
        """
        try:
            logger.info(f"Weather request: location='{location}'")
            
            # Create and validate request
            request = WeatherRequest(location=location)
            
            # Get weather data
            response = await weather_service.get_weather(request.location)
            
            logger.info(
                f"Weather response: location='{location}' -> "
                f"{response.current_conditions.temperature.value}°C, "
                f"{response.current_conditions.weather}"
            )
            
            return response
            
        except ValueError as e:
            # Handle validation errors
            error_msg = str(e)
            logger.warning(f"Weather request validation error: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid location format: {error_msg}"
            )
        except HTTPException:
            # Re-raise HTTP exceptions (404, 503, etc.)
            logger.warning(f"Weather service HTTP error for location '{location}'")
            raise
        except Exception as e:
            # Catch all other errors
            logger.error(f"Weather service error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Weather service unavailable: {str(e)}"
            )
    
    return router