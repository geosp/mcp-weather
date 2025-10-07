"""
MCP tool definitions for Weather service

Defines the tools that AI assistants can call via the Model Context Protocol.
Each tool is a wrapper around the WeatherService with authentication.
"""

import logging
from typing import Dict, Any

from fastmcp import FastMCP

from .weather_service import WeatherService
from .models import WeatherResponse

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, weather_service: WeatherService) -> None:
    """
    Register all weather tools with the MCP server
    
    This function defines and registers MCP tools that AI assistants can call.
    All tools require authentication via the auth provider configured on the mcp instance.
    
    Args:
        mcp: FastMCP server instance
        weather_service: WeatherService instance for fetching data
        
    Note:
        Authentication is handled by the FastMCP auth provider.
        Tools are automatically documented in the MCP protocol.
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
        
        Example Response:
            {
                "location": "Tallahassee",
                "country": "United States",
                "coordinates": {
                    "latitude": 30.4383,
                    "longitude": -84.2807
                },
                "timezone": "America/New_York",
                "current_conditions": {
                    "temperature": {"value": 22.5, "unit": "°C"},
                    "feels_like": {"value": 21.8, "unit": "°C"},
                    "humidity": {"value": 65, "unit": "%"},
                    "precipitation": {"value": 0.0, "unit": "mm"},
                    "wind": {
                        "speed": 15.3,
                        "direction": "WSW",
                        "direction_degrees": 245.0,
                        "unit": "km/h"
                    },
                    "weather": "Partly cloudy",
                    "time": "2024-01-15T14:30:00"
                },
                "hourly_forecast": [
                    {
                        "time": "2024-01-15T15:00:00",
                        "temperature": {"value": 23.0, "unit": "°C"},
                        "precipitation_probability": {"value": 20, "unit": "%"},
                        "precipitation": {"value": 0.1, "unit": "mm"},
                        "weather": "Partly cloudy",
                        "wind_speed": {"value": 12.5, "unit": "km/h"}
                    }
                    // ... 11 more hourly entries
                ],
                "data_source": "Open-Meteo API (https://open-meteo.com)"
            }
        
        Notes:
            - Location names are case-insensitive
            - Coordinates are cached for 30 days to reduce API calls
            - Weather data updates every ~15 minutes from Open-Meteo
            - All temperatures in Celsius, wind in km/h
            - Times are in the location's local timezone
        """
        try:
            logger.info(f"MCP tool called: get_hourly_weather(location='{location}')")
            
            # Call weather service
            weather_response: WeatherResponse = await weather_service.get_weather(location)
            
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
            logger.error(
                f"MCP tool error in get_hourly_weather('{location}'): {e}",
                exc_info=True
            )
            raise
    
    logger.info("Registered MCP tools: get_hourly_weather")


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions of all available tools
    
    Useful for generating documentation or help text.
    
    Returns:
        Dict mapping tool names to their descriptions
    """
    return {
        "get_hourly_weather": (
            "Get hourly weather forecast for a location. "
            "Provides current conditions and 12-hour forecast from Open-Meteo API. "
            "Requires location name (e.g., 'Tallahassee', 'London'). "
            "Returns temperature, humidity, wind, precipitation, and weather descriptions."
        )
    }


def get_tool_examples() -> Dict[str, list]:
    """
    Get example usages for all tools
    
    Useful for AI assistants to understand how to call tools effectively.
    
    Returns:
        Dict mapping tool names to lists of example calls
    """
    return {
        "get_hourly_weather": [
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