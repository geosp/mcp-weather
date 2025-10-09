"""
Weather service for interacting with Open-Meteo API

Handles geocoding, weather data fetching, and data transformation.
Provides clean abstraction over the Open-Meteo API.
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional

from aiohttp import ClientSession, ClientError, ClientTimeout
from fastapi import HTTPException

from core.cache import RedisCacheClient
from mcp_weather.config import WeatherAPIConfig
from mcp_weather.models import (
    LocationData,
    WeatherResponse,
    CurrentConditions,
    HourlyForecast,
    Coordinates,
    Measurement,
    WindData
)

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Handles all weather API interactions using Open-Meteo API
    
    This service provides a complete weather data pipeline:
    1. Location validation and sanitization
    2. Geocoding (location name -> coordinates) with caching
    3. Weather data fetching from Open-Meteo API
    4. Data formatting and standardization
    5. Weather code translation to human-readable descriptions
    
    Features:
        - Free Open-Meteo API (no API key required)
        - Location coordinate caching with expiry (30 days)
        - Comprehensive error handling and validation
        - WMO weather code translation
        - Wind direction formatting
        - Structured response models
    
    APIs Used:
        - Open-Meteo Geocoding API: https://geocoding-api.open-meteo.com/v1/search
        - Open-Meteo Weather API: https://api.open-meteo.com/v1/forecast
    """
    
    # WMO Weather Code Mappings
    WEATHER_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    
    # Cardinal directions for wind
    WIND_DIRECTIONS = [
        "N", "NNE", "NE", "ENE", 
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", 
        "W", "WNW", "NW", "NNW"
    ]
    
    def __init__(self, api_config: WeatherAPIConfig, cache_client: RedisCacheClient):
        """
        Initialize weather service
        
        Args:
            api_config: Weather API configuration with endpoint URLs
            cache_client: Redis cache client for storing geocoded coordinates
        """
        self.geocoding_url = api_config.geocoding_url
        self.weather_url = api_config.weather_url
        self.cache_client = cache_client
        
        # HTTP client timeout configuration
        self.timeout = ClientTimeout(total=30, connect=10)
        
        logger.info(
            f"Initialized WeatherService with geocoding={self.geocoding_url}, "
            f"weather={self.weather_url}"
        )
    
    def _validate_location(self, location: str) -> str:
        """
        Validate and sanitize location input
        
        Args:
            location: Raw location string from user
            
        Returns:
            Sanitized location string
            
        Raises:
            ValueError: If location is empty or too long
        """
        if not location or not location.strip():
            raise ValueError("Location cannot be empty")
        
        location = location.strip()
        
        if len(location) > 100:
            raise ValueError("Location name too long (max 100 characters)")
        
        return location
    
    def _format_weather_code(self, code: int) -> str:
        """
        Convert WMO weather code to human-readable description
        
        Args:
            code: WMO weather code (0-99)
            
        Returns:
            Weather description string
        """
        return self.WEATHER_CODES.get(code, f"Unknown ({code})")
    
    def _format_wind_direction(self, degrees: float) -> str:
        """
        Convert wind direction degrees to cardinal direction
        
        Args:
            degrees: Wind direction in degrees (0-360)
            
        Returns:
            Cardinal direction (N, NE, E, SE, etc.)
        """
        if degrees < 0 or degrees > 360:
            return "Unknown"
        
        idx = int((degrees + 11.25) / 22.5) % 16
        return self.WIND_DIRECTIONS[idx]
    
    # Dictionary of U.S. state abbreviations to full names
    US_STATES = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", 
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", 
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", 
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", 
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", 
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", 
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", 
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", 
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", 
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", 
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", 
        "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
    }
    
    # Reverse mapping from state names to abbreviations
    US_STATES_REVERSE = {v.lower(): k for k, v in US_STATES.items()}
    
    # Country name variations to standardize country references
    COUNTRY_VARIATIONS = {
        "us": "United States",
        "usa": "United States",
        "u.s.": "United States",
        "u.s.a.": "United States",
        "united states of america": "United States",
        "uk": "United Kingdom",
        "u.k.": "United Kingdom",
        "gb": "United Kingdom",  # Great Britain
        "uae": "United Arab Emirates",
        "u.a.e.": "United Arab Emirates",
        "ca": "Canada",
        "can": "Canada"
    }

    def _parse_location(self, location: str) -> tuple[str, Optional[str], Optional[str]]:
        """
        Parse a location string into city, state/province, and country components
        
        Args:
            location: Location string (e.g., "Vancouver, Canada" or "Cleveland, GA, USA")
            
        Returns:
            Tuple of (city, state, country), where state and country may be None
        """
        parts = [p.strip() for p in location.split(',')]
        
        city = parts[0]
        state = None
        country = None
        
        if len(parts) == 2:
            # Format: "City, Country" or "City, State"
            second_part = parts[1]
            
            # Check if second part is a U.S. state abbreviation
            if second_part.upper() in self.US_STATES:
                state = second_part
                country = "United States"
            # Check if second part is a full U.S. state name
            elif second_part.lower() in self.US_STATES_REVERSE:
                state = self.US_STATES_REVERSE[second_part.lower()]
                country = "United States"
            # Check if second part is a country abbreviation or variant
            elif second_part.lower() in self.COUNTRY_VARIATIONS:
                country = self.COUNTRY_VARIATIONS[second_part.lower()]
            else:
                country = second_part
                
        elif len(parts) >= 3:
            # Format: "City, State, Country"
            state_part = parts[1]
            country_part = parts[2]
            
            # Check if the state part is a full state name, convert to abbreviation if so
            if state_part.lower() in self.US_STATES_REVERSE:
                state = self.US_STATES_REVERSE[state_part.lower()]
            else:
                state = state_part
                
            # Normalize country name if it's a known variant
            if country_part.lower() in self.COUNTRY_VARIATIONS:
                country = self.COUNTRY_VARIATIONS[country_part.lower()]
            else:
                country = country_part
            
            # If we have more than 3 parts, combine the rest into the country
            if len(parts) > 3:
                country = ", ".join(parts[2:])
                
        # Log the parsed components for debugging
        logger.info(f"Parsed location '{location}' into city='{city}', state='{state}', country='{country}'")
        
        return city, state, country

    async def _geocode_location(
        self, 
        session: ClientSession, 
        location: str
    ) -> LocationData:
        """
        Convert location name to coordinates using Open-Meteo Geocoding API
        
        Args:
            session: aiohttp client session
            location: Location name to geocode
            
        Returns:
            LocationData with coordinates and metadata
            
        Raises:
            HTTPException: 404 if location not found, 500 for API errors
        """
        # Parse location components for better geocoding accuracy
        city, state, country = self._parse_location(location)
        
        # Build the query based on the parsed components
        query = city
        if state:
            # For US locations, just use city name and filter by state later
            pass
        elif country:
            # For international locations, use city + normalized country
            query = f"{city}"  # Don't include country in query, we'll filter by country later
        
        # Set up basic parameters
        params = {
            "name": query,
            "count": 10,  # Request more results to filter
            "language": "en",
            "format": "json"
        }
        
        logger.info(f"Geocoding query: {params['name']}")
        
        try:
            async with session.get(
                self.geocoding_url, 
                params=params,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(
                        f"Geocoding API error: HTTP {resp.status}",
                        extra={"response": text[:200]}
                    )
                    raise HTTPException(
                        status_code=resp.status,
                        detail=f"Geocoding failed: {text[:100]}"
                    )
                
                data = await resp.json()
                results = data.get("results")
                
                if not results:
                    logger.warning(f"Location not found: {location}")
                    raise HTTPException(
                        status_code=404,
                        detail=f"Location not found: {location}"
                    )
                
                # Log raw API response for debugging
                logger.debug(f"Geocoding API returned {len(results)} results")
                
                # Get parsed components
                city, state, country = self._parse_location(location)
                
                # Filter results to prioritize exact matches
                filtered_results = []
                
                # Debug log all results for better debugging
                for i, r in enumerate(results):
                    admin1 = r.get("admin1", "")  # State/Province
                    logger.info(f"Result {i+1}: {r.get('name')}, {admin1}, {r.get('country')} ({r.get('latitude')}, {r.get('longitude')})")
                
                # Case 1: US location with state specified
                if state and country and "united states" in country.lower():
                    logger.info(f"Filtering results for US city='{city}', state='{state}'")
                    
                    # Get full state name regardless of whether state is abbreviation or full name
                    if state.upper() in self.US_STATES:
                        state_full = self.US_STATES.get(state.upper(), state)
                        state_abbr = state.upper()
                    else:
                        # Handle case where state is already the full name
                        state_lower = state.lower()
                        state_abbr = self.US_STATES_REVERSE.get(state_lower, state)
                        state_full = self.US_STATES.get(state_abbr, state)
                    
                    logger.info(f"Processed state: abbreviation='{state_abbr}', full name='{state_full}'")
                    
                    # First priority: Exact city name + exact state match
                    for r in results:
                        r_city = r.get("name", "").lower()
                        r_admin1 = r.get("admin1", "").lower()  # State
                        r_country = r.get("country", "").lower()
                        
                        if (r_city == city.lower() and 
                            "united states" in r_country.lower() and
                            (state_full.lower() in r_admin1 or 
                             state_abbr.lower() in r_admin1 or
                             state.lower() in r_admin1)):
                            logger.info(f"Found exact US state match: {r.get('name')}, {r.get('admin1')}")
                            filtered_results.append(r)
                            break  # Use the first exact match
                
                # Case 2: International location with country specified
                elif country:
                    logger.info(f"Filtering results for international city='{city}', country='{country}'")
                    
                    # Handle US country variations specially
                    is_us_query = False
                    if country.lower() == "united states" or country.lower() in ["us", "usa", "u.s.", "u.s.a."]:
                        is_us_query = True
                    
                    # Look for exact city+country match first (case-insensitive)
                    for r in results:
                        r_country = r.get("country", "").lower()
                        r_city = r.get("name", "").lower()
                        
                        # Direct match for city, flexible match for country
                        country_match = False
                        if is_us_query:
                            # For US, match variations of United States
                            country_match = "united states" in r_country
                        else:
                            # For other countries, do a more flexible match
                            country_match = (country.lower() in r_country or 
                                           r_country in country.lower())
                        
                        if r_city == city.lower() and country_match:
                            logger.info(f"Found exact international match: {r.get('name')}, {r.get('country')}")
                            filtered_results.append(r)
                    
                    # If no exact matches, try country matches with similar city names
                    if not filtered_results:
                        for r in results:
                            r_country = r.get("country", "").lower()
                            
                            # More flexible country matching
                            country_match = False
                            if is_us_query:
                                country_match = "united states" in r_country
                            else:
                                country_match = (country.lower() in r_country or 
                                               r_country in country.lower())
                                
                            if country_match:
                                logger.info(f"Found country match: {r.get('name')}, {r.get('country')}")
                                filtered_results.append(r)
                
                # If we found matches, use the first filtered result
                # Otherwise use the first API result
                if filtered_results:
                    logger.info(f"Using filtered result: {filtered_results[0].get('name')}, {filtered_results[0].get('country')}")
                    result = filtered_results[0]
                else:
                    logger.info(f"No filtered matches, using first result: {results[0].get('name')}, {results[0].get('country')}")
                    result = results[0]
                
                location_data = LocationData(
                    latitude=result["latitude"],
                    longitude=result["longitude"],
                    name=result["name"],
                    country=result.get("country", ""),
                    timezone=result.get("timezone", "auto")
                )
                
                logger.info(
                    f"Geocoded {location} -> {location_data.name}, "
                    f"{location_data.country} ({location_data.latitude}, {location_data.longitude})"
                )
                
                return location_data
                
        except HTTPException:
            raise
        except ClientError as e:
            logger.error(f"Geocoding network error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Geocoding service unavailable"
            )
        except Exception as e:
            logger.error(f"Geocoding unexpected error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Geocoding service error"
            )
    
    async def _fetch_weather(
        self,
        session: ClientSession,
        latitude: float,
        longitude: float,
        timezone: str = "auto"
    ) -> Dict[str, Any]:
        """
        Fetch weather data from Open-Meteo API
        
        Args:
            session: aiohttp client session
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            timezone: Timezone identifier or "auto"
            
        Returns:
            Raw weather data dictionary from API
            
        Raises:
            HTTPException: For API errors or network issues
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                      "precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "hourly": "temperature_2m,precipitation_probability,precipitation,"
                     "weather_code,wind_speed_10m",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timezone": timezone,
            "forecast_days": 1
        }
        
        try:
            async with session.get(
                self.weather_url,
                params=params,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(
                        f"Weather API error: HTTP {resp.status}",
                        extra={"response": text[:200]}
                    )
                    raise HTTPException(
                        status_code=resp.status,
                        detail=f"Weather fetch failed: {text[:100]}"
                    )
                
                data = await resp.json()
                logger.debug(f"Fetched weather data for ({latitude}, {longitude})")
                return data
                
        except HTTPException:
            raise
        except ClientError as e:
            logger.error(f"Weather API network error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Weather service unavailable"
            )
        except Exception as e:
            logger.error(f"Weather API unexpected error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Weather service error"
            )
    
    def _build_current_conditions(self, current_data: Dict[str, Any]) -> CurrentConditions:
        """
        Build CurrentConditions model from API data
        
        Args:
            current_data: Current weather data from API
            
        Returns:
            CurrentConditions model instance
        """
        return CurrentConditions(
            temperature=Measurement(
                value=current_data.get("temperature_2m"),
                unit="°C"
            ),
            feels_like=Measurement(
                value=current_data.get("apparent_temperature"),
                unit="°C"
            ),
            humidity=Measurement(
                value=current_data.get("relative_humidity_2m"),
                unit="%"
            ),
            precipitation=Measurement(
                value=current_data.get("precipitation"),
                unit="mm"
            ),
            wind=WindData(
                speed=current_data.get("wind_speed_10m"),
                direction_degrees=current_data.get("wind_direction_10m"),
                direction=self._format_wind_direction(
                    current_data.get("wind_direction_10m", 0)
                ),
                unit="km/h"
            ),
            weather=self._format_weather_code(
                current_data.get("weather_code", 0)
            ),
            time=current_data.get("time", "")
        )
    
    def _build_hourly_forecast(self, hourly_data: Dict[str, Any]) -> List[HourlyForecast]:
        """
        Build list of HourlyForecast models from API data
        
        Args:
            hourly_data: Hourly weather data from API
            
        Returns:
            List of HourlyForecast models (next 12 hours)
        """
        forecast = []
        
        if not hourly_data or "time" not in hourly_data:
            return forecast
        
        # Extract arrays (limit to 12 hours)
        times = hourly_data.get("time", [])[:12]
        temps = hourly_data.get("temperature_2m", [])[:12]
        precip_prob = hourly_data.get("precipitation_probability", [])[:12]
        precip = hourly_data.get("precipitation", [])[:12]
        weather_codes = hourly_data.get("weather_code", [])[:12]
        wind_speeds = hourly_data.get("wind_speed_10m", [])[:12]
        
        # Build forecast entries
        for i, time in enumerate(times):
            forecast.append(
                HourlyForecast(
                    time=time,
                    temperature=Measurement(
                        value=temps[i] if i < len(temps) else None,
                        unit="°C"
                    ),
                    precipitation_probability=Measurement(
                        value=precip_prob[i] if i < len(precip_prob) else None,
                        unit="%"
                    ),
                    precipitation=Measurement(
                        value=precip[i] if i < len(precip) else None,
                        unit="mm"
                    ),
                    weather=self._format_weather_code(
                        weather_codes[i] if i < len(weather_codes) else 0
                    ),
                    wind_speed=Measurement(
                        value=wind_speeds[i] if i < len(wind_speeds) else None,
                        unit="km/h"
                    )
                )
            )
        
        return forecast
    
    async def get_weather(self, location: str) -> WeatherResponse:
        """
        Get complete weather information for a location
        
        This is the main public method that orchestrates the entire workflow:
        1. Validate location
        2. Check cache for coordinates
        3. Geocode if not cached
        4. Fetch weather data
        5. Transform to response model
        
        Args:
            location: City name (e.g., "Tallahassee", "New York", "London")
            
        Returns:
            WeatherResponse with location info, current conditions, and forecast
            
        Raises:
            ValueError: If location is invalid
            HTTPException: If geocoding or weather fetch fails
        """
        # Validate input
        location = self._validate_location(location)
        logger.info(f"Fetching weather for: {location}")
        
        # Check cache for coordinates
        cached_location = await self.cache_client.get(location, LocationData.from_dict)
        
        async with ClientSession() as session:
            # Get location coordinates (from cache or API)
            if cached_location:
                logger.info(f"Using cached coordinates for {location}")
                location_data = cached_location
            else:
                logger.info(f"Cache miss, geocoding {location}")
                location_data = await self._geocode_location(session, location)
                # Cache the result as a dictionary
                await self.cache_client.set(location, location_data.to_dict())
            
            # Fetch weather data
            weather_data = await self._fetch_weather(
                session,
                location_data.latitude,
                location_data.longitude,
                location_data.timezone
            )
        
        # Extract and transform data
        current_data = weather_data.get("current", {})
        hourly_data = weather_data.get("hourly", {})
        
        current_conditions = self._build_current_conditions(current_data)
        hourly_forecast = self._build_hourly_forecast(hourly_data)
        
        # Build response
        response = WeatherResponse(
            location=location_data.name,
            country=location_data.country,
            coordinates=Coordinates(
                latitude=location_data.latitude,
                longitude=location_data.longitude
            ),
            timezone=weather_data.get("timezone", "UTC"),
            current_conditions=current_conditions,
            hourly_forecast=hourly_forecast
        )
        
        logger.info(
            f"Successfully fetched weather for {location}: "
            f"{current_conditions.temperature.value}°C, {current_conditions.weather}"
        )
        
        return response