"""
Geocoding Tool Implementation

Provides the geocode_location tool for converting locations into
coordinates through the MCP protocol.
"""

import logging
from typing import Dict, Any

from aiohttp import ClientSession
from fastmcp import FastMCP

from core.utils import inject_docstring, load_instruction
from mcp_weather.geocoding_service import GeocodingService
from mcp_weather.features.geocoding.models import GeocodingResponse

logger = logging.getLogger(__name__)

def register_tool(mcp: FastMCP, geocoding_service: GeocodingService) -> None:
    """
    Register the geocode_location tool with the MCP server
    
    Args:
        mcp: FastMCP server instance
        geocoding_service: GeocodingService instance for geocoding
    """
    @mcp.tool()
    @inject_docstring(lambda: load_instruction("instructions.md", __file__))
    async def geocode_location(location: str) -> Dict[str, Any]:
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