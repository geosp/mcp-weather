"""
Hourly Weather Tool Implementation

Provides the get_hourly_weather tool for accessing weather forecasts
through the MCP protocol.
"""

import logging
from typing import Dict, Any

from fastmcp import FastMCP

from core.utils import inject_docstring, load_instruction
from mcp_weather.weather_service import WeatherService
from mcp_weather.features.hourly_weather.models import WeatherResponse, WeatherRequest

logger = logging.getLogger(__name__)

def register_tool(mcp: FastMCP, weather_service: WeatherService) -> None:
    """
    Register the get_hourly_weather tool with the MCP server
    
    Args:
        mcp: FastMCP server instance
        weather_service: WeatherService instance for fetching data
    """
    @mcp.tool()
    @inject_docstring(lambda: load_instruction("instructions.md", __file__))
    async def get_hourly_weather(location: str) -> Dict[str, Any]:
        try:
            logger.info(f"MCP tool called: get_hourly_weather(location='{location}')")
            
            # Create and validate request
            request = WeatherRequest(location=location)
            
            # Call weather service
            weather_response: WeatherResponse = await weather_service.get_weather(request.location)
            
            # Convert Pydantic model to dict for MCP response
            result = weather_response.model_dump()
            
            logger.info(
                f"MCP tool completed: get_hourly_weather('{location}') -> "
                f"{weather_response.current_conditions.temperature.value}°C"
            )
            
            return result
            
        except ValueError as e:
            # Invalid location format
            logger.warning(f"MCP tool validation error: {e}")
            raise
        except Exception as e:
            # Log error but let it propagate to MCP framework
            logger.error(f"MCP tool error in get_hourly_weather('{location}'): {e}")
            raise