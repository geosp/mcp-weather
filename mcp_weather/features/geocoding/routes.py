"""
API routes for the geocoding feature
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from aiohttp import ClientSession

from core.auth_rest import get_token_from_header
from mcp_weather.geocoding_service import GeocodingService
from mcp_weather.features.geocoding.models import GeocodingRequest, GeocodingResponse

logger = logging.getLogger(__name__)

def create_router(geocoding_service: GeocodingService) -> APIRouter:
    """
    Create a router for the geocoding feature
    
    Args:
        geocoding_service: GeocodingService instance for geocoding locations
        
    Returns:
        FastAPI router with geocoding endpoints
    """
    # Create the router for the geocoding feature
    router = APIRouter(
        prefix="/geocoding",
        tags=["geocoding"],
        responses={
            404: {"description": "Location not found"},
            400: {"description": "Invalid request"},
            500: {"description": "Server error"}
        }
    )


    @router.post("/", response_model=GeocodingResponse, summary="Geocode a location")
    async def geocode_location(
        request: GeocodingRequest,
        token: str = Depends(get_token_from_header)
    ):
        """
        Geocode a location name to coordinates and timezone information
        
        This endpoint takes a location string (e.g., city name, city and country) and
        returns the resolved coordinates, timezone, and standardized location name.
        
        Examples:
            - "Paris"
            - "Tokyo, Japan"
            - "Miami, FL"
            - "Vancouver, BC, Canada"
            - "London, Ontario, Canada"
            
        Returns:
            GeocodingResponse with location details
        """
        location = request.location
        
        try:
            async with ClientSession() as session:
                location_data = await geocoding_service.get_location_coordinates(session, location)
                
                return GeocodingResponse(
                    location=location_data.name,
                    country=location_data.country,
                    coordinates={
                        "latitude": location_data.latitude,
                        "longitude": location_data.longitude
                    },
                    timezone=location_data.timezone
                )
        except ValueError as e:
            logger.error(f"Invalid location format: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise  # Re-raise existing HTTPExceptions
        except Exception as e:
            logger.error(f"Error geocoding location: {e}")
            raise HTTPException(status_code=500, detail="Error geocoding location")
    
    return router