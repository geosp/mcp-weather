"""
Hourly Weather Tool Implementation

Provides the get_hourly_weather tool for accessing weather forecasts
through the MCP protocol.
"""

import logging
from typing import Dict, Any

from fastmcp import FastMCP

from ...weather_service import WeatherService
from .models import WeatherResponse, WeatherRequest

logger = logging.getLogger(__name__)

# Tool metadata for documentation and discovery
tool_metadata = {
    "name": "get_hourly_weather",
    "description": (
        "Get hourly weather forecast for a location using Open-Meteo API\n\n"
        "This tool provides comprehensive weather data for AI assistants to help users\n"
        "with weather queries. It requires authentication via Bearer token.\n\n"
        "The tool returns current conditions plus a 12-hour forecast, making it suitable\n"
        "for answering questions like:\n"
        "- \"What's the weather in Paris?\"\n"
        "- \"Will it rain in Tokyo today?\"\n"
        "- \"What's the temperature in New York right now?\"\n"
        "- \"Should I bring an umbrella in London?\""
    ),
    "examples": [
        {
            "description": "Get weather for a major city",
            "call": "get_hourly_weather('London')",
            "use_case": "User asks 'What's the weather in London?'"
        },
        {
            "description": "Get weather with country specification",
            "call": "get_hourly_weather('Paris, France')",
            "use_case": "User asks 'How's the weather in Paris?'"
        },
        {
            "description": "Get weather for trip planning",
            "call": "get_hourly_weather('Tokyo')",
            "use_case": "User asks 'Should I bring an umbrella to Tokyo today?'"
        },
        {
            "description": "Get weather for current location",
            "call": "get_hourly_weather('Tallahassee')",
            "use_case": "User asks 'What's the temperature here?' (if context is Tallahassee)"
        }
    ]
}

def register_tool(mcp: FastMCP, weather_service: WeatherService) -> None:
    """
    Register the get_hourly_weather tool with the MCP server
    
    Args:
        mcp: FastMCP server instance
        weather_service: WeatherService instance for fetching data
    """
    @mcp.tool()
    async def get_hourly_weather(location: str) -> Dict[str, Any]:
        """
        Get hourly weather forecast for a location using Open-Meteo API
        
        This tool provides comprehensive weather data for AI assistants to help users
        with weather queries. It requires authentication via Bearer token.
        
        The tool returns current conditions plus a 12-hour forecast, making it suitable
        for answering questions like:
        - "What's the weather in Paris?"
        - "Will it rain in Tokyo today?"
        - "What's the temperature in New York right now?"
        - "Should I bring an umbrella in London?"
        
        Features:
            - Current temperature, humidity, wind, and precipitation
            - 12-hour hourly forecast
            - Weather descriptions in plain English
            - Wind direction in cardinal directions (N, NE, E, etc.)
            - Location caching for performance
            - No API key required (uses free Open-Meteo API)
        
        Authentication:
            Requires valid Authentik Bearer token in Authorization header.
            The MCP framework handles authentication automatically.
        
        Data Source:
            Open-Meteo API (https://open-meteo.com)
            - Free, no API key required
            - Updates every 15 minutes
            - Covers worldwide locations
        
        Args:
            location (str): City name or location identifier
                Examples: "Tallahassee", "New York", "London", "Tokyo", "Paris, France"
                Can be just city name or "City, Country" format
                
        Returns:
            Dict[str, Any]: Structured weather data containing:
                - location: Location name and coordinates
                - country: Country name
                - timezone: Local timezone
                - current_conditions: Current weather snapshot with:
                    - temperature (°C)
                    - feels_like (°C)
                    - humidity (%)
                    - precipitation (mm)
                    - wind (speed, direction)
                    - weather description
                - hourly_forecast: List of 12 hourly forecasts with:
                    - time (ISO format)
                    - temperature (°C)
                    - precipitation probability (%)
                    - precipitation amount (mm)
                    - weather description
                    - wind speed (km/h)
                - data_source: Attribution to Open-Meteo API
        
        Raises:
            ValueError: If location is empty or invalid format
            HTTPException: 404 if location not found
            HTTPException: 503 if weather service unavailable
            AuthenticationError: If Bearer token is missing or invalid (handled by MCP)
        
        Example Usage (in AI conversation):
            User: "What's the weather like in Tallahassee?"
            
            AI calls: get_hourly_weather("Tallahassee")
            
            AI responds: "In Tallahassee, it's currently 22.5°C (feels like 21.8°C) 
                         with partly cloudy skies. Humidity is 65% with light winds 
                         from the west-southwest at 15 km/h. No precipitation expected 
                         in the next few hours."
        
        Notes:
            - Location names are case-insensitive
            - Coordinates are cached for 30 days to reduce API calls
            - Weather data updates every ~15 minutes from Open-Meteo
            - All temperatures in Celsius, wind in km/h
            - Times are in the location's local timezone
        """
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