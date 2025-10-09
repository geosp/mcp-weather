"""
Geocoding Tool Implementation

Provides the geocode_location tool for converting locations into
coordinates through the MCP protocol.
"""

import logging
from typing import Dict, Any

from aiohttp import ClientSession
from fastmcp import FastMCP

from mcp_weather.geocoding_service import GeocodingService
from mcp_weather.features.geocoding.models import GeocodingResponse

logger = logging.getLogger(__name__)

# Tool metadata for documentation and discovery
tool_metadata = {
    "name": "geocode_location",
    "description": "Get coordinates and timezone information for a location. "
                  "This tool converts a city or address into geographic coordinates "
                  "and timezone, useful for mapping applications, travel planning, "
                  "and local time calculations.",
    "examples": [
        {
            "description": "Get coordinates for a major city",
            "call": "geocode_location('London')",
            "use_case": "User asks 'What are the coordinates of London?'"
        },
        {
            "description": "Get timezone for location with country specification",
            "call": "geocode_location('Vancouver, Canada')",
            "use_case": "User asks 'What timezone is Vancouver, Canada in?'"
        }
    ]
}

def register_tool(mcp: FastMCP, geocoding_service: GeocodingService) -> None:
    """
    Register the geocode_location tool with the MCP server
    
    Args:
        mcp: FastMCP server instance
        geocoding_service: GeocodingService instance for geocoding
    """
    @mcp.tool()
    async def geocode_location(location: str) -> Dict[str, Any]:
        """
        Get coordinates and timezone information for a location.
        
        This tool converts a city or address into geographic coordinates and timezone, 
        useful for mapping applications, travel planning, and local time calculations.
        
        Examples:
        - "Paris, France"
        - "Tokyo"
        - "New York, NY"
        - "Vancouver, BC, Canada"
        
        Args:
            location: The location to geocode (city name, address, etc.)
            
        Returns:
            Dictionary with location data (name, country, coordinates, timezone)
        """
        try:
            logger.info(f"Processing geocoding request for: {location}")
            
            async with ClientSession() as session:
                location_data = await geocoding_service.get_location_coordinates(session, location)
                
                result = {
                    "location": location_data.name,
                    "country": location_data.country,
                    "coordinates": {
                        "latitude": location_data.latitude,
                        "longitude": location_data.longitude
                    },
                    "timezone": location_data.timezone
                }
                
                logger.info(f"Geocoded {location} to {location_data.name}, {location_data.country}")
                return result
                
        except ValueError as e:
            logger.error(f"MCP tool validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"MCP tool error in geocode_location('{location}'): {e}")
            raise