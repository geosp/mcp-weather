Get hourly weather forecast for a location using Open-Meteo API

This tool provides comprehensive weather data for AI assistants to help users
with weather queries. It requires authentication via Bearer token.

The tool returns current conditions plus a 12-hour forecast, making it suitable
for answering questions like:
- "What's the weather in Paris?"
- "Will it rain in Tokyo today?"
- "What's the temperature in New York right now?"
- "Should I bring an umbrella in London?"
- "How cold is it in Vancouver, Canada?"

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
        Examples: "Tallahassee", "New York", "London, UK", "Tokyo, Japan", "Vancouver, Canada"
        Can be just city name or "City, Country" format (recommended for cities with same name)
        
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