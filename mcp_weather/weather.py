import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta

from fastmcp import FastMCP
from dotenv import load_dotenv
from aiohttp import ClientSession
from fastapi import FastAPI, HTTPException
from starlette.routing import Mount
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("mcp-weather")

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "weather"
LOCATION_CACHE_FILE = CACHE_DIR / "location_cache.json"
CACHE_EXPIRY_DAYS = 30


class LocationCache:
    """Handles caching of location coordinates with expiry"""
    
    @staticmethod
    def get(location: str) -> Optional[Dict[str, float]]:
        """Get cached location coordinates if they exist and haven't expired"""
        if not LOCATION_CACHE_FILE.exists():
            return None
        
        try:
            with open(LOCATION_CACHE_FILE, "r") as f:
                cache = json.load(f)
                entry = cache.get(location.lower())
                
                if not entry:
                    return None
                
                # Check if entry has expired
                if isinstance(entry, dict) and "cached_at" in entry:
                    cached_at = entry.get("cached_at")
                    if cached_at:
                        cache_age = datetime.now() - datetime.fromisoformat(cached_at)
                        if cache_age > timedelta(days=CACHE_EXPIRY_DAYS):
                            logger.info(f"Cache expired for {location}")
                            return None
                        return {
                            "latitude": entry.get("latitude"),
                            "longitude": entry.get("longitude"),
                            "name": entry.get("name"),
                            "country": entry.get("country")
                        }
                
                return None
                
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None
    
    @staticmethod
    def set(location: str, data: Dict[str, Any]):
        """Cache location data with timestamp"""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            cache = {}
            if LOCATION_CACHE_FILE.exists():
                with open(LOCATION_CACHE_FILE, "r") as f:
                    cache = json.load(f)
            
            cache[location.lower()] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "name": data["name"],
                "country": data.get("country", ""),
                "cached_at": datetime.now().isoformat()
            }
            
            # Atomic write
            temp_file = LOCATION_CACHE_FILE.with_suffix('.tmp')
            with open(temp_file, "w") as f:
                json.dump(cache, f, indent=2)
            temp_file.replace(LOCATION_CACHE_FILE)
            
            logger.info(f"Cached location data for {location}")
            
        except Exception as e:
            logger.error(f"Failed to cache location data: {e}")


class WeatherService:
    """Handles all weather API interactions using Open-Meteo"""
    
    def __init__(self):
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
    
    def _validate_location(self, location: str) -> str:
        """Validate and sanitize location input"""
        if not location or not location.strip():
            raise ValueError("Location cannot be empty")
        
        location = location.strip()
        if len(location) > 100:
            raise ValueError("Location name too long (max 100 characters)")
        
        return location
    
    async def _geocode_location(self, session: ClientSession, location: str) -> Dict[str, Any]:
        """Convert location name to coordinates using Open-Meteo Geocoding API"""
        params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        async with session.get(self.geocoding_url, params=params) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise HTTPException(
                    status_code=resp.status,
                    detail=f"Geocoding failed: {text}"
                )
            
            data = await resp.json()
            results = data.get("results")
            
            if not results:
                raise HTTPException(
                    status_code=404,
                    detail=f"Location not found: {location}"
                )
            
            result = results[0]
            return {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "name": result["name"],
                "country": result.get("country", ""),
                "timezone": result.get("timezone", "auto")
            }
    
    async def _fetch_weather(self, session: ClientSession, latitude: float, longitude: float, timezone: str = "auto") -> Dict[str, Any]:
        """Fetch weather data from Open-Meteo API"""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timezone": timezone,
            "forecast_days": 1
        }
        
        async with session.get(self.weather_url, params=params) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise HTTPException(
                    status_code=resp.status,
                    detail=f"Weather fetch failed: {text}"
                )
            
            return await resp.json()
    
    def _format_weather_code(self, code: int) -> str:
        """Convert WMO weather code to description"""
        weather_codes = {
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
        return weather_codes.get(code, f"Unknown ({code})")
    
    def _format_wind_direction(self, degrees: float) -> str:
        """Convert wind direction degrees to cardinal direction"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = int((degrees + 11.25) / 22.5) % 16
        return directions[idx]
    
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get complete weather information for a location
        
        Args:
            location: City name (e.g., "Tallahassee", "New York", "London")
            
        Returns:
            Dictionary containing location info, current conditions, and hourly forecast
        """
        location = self._validate_location(location)
        logger.info(f"Fetching weather for: {location}")
        
        # Check cache
        cached_location = LocationCache.get(location)
        
        async with ClientSession() as session:
            # Get location coordinates
            if not cached_location:
                logger.info(f"Cache miss for {location}, geocoding...")
                location_data = await self._geocode_location(session, location)
                LocationCache.set(location, location_data)
            else:
                logger.info(f"Cache hit for {location}")
                location_data = cached_location
                # Use cached timezone if available
                if "timezone" not in location_data:
                    location_data["timezone"] = "auto"
            
            # Fetch weather data
            weather_data = await self._fetch_weather(
                session,
                location_data["latitude"],
                location_data["longitude"],
                location_data.get("timezone", "auto")
            )
        
        # Format the response
        current = weather_data.get("current", {})
        hourly = weather_data.get("hourly", {})
        
        # Format current conditions
        current_conditions = {
            "temperature": {
                "value": current.get("temperature_2m"),
                "unit": "°C"
            },
            "feels_like": {
                "value": current.get("apparent_temperature"),
                "unit": "°C"
            },
            "humidity": {
                "value": current.get("relative_humidity_2m"),
                "unit": "%"
            },
            "precipitation": {
                "value": current.get("precipitation"),
                "unit": "mm"
            },
            "wind": {
                "speed": current.get("wind_speed_10m"),
                "direction_degrees": current.get("wind_direction_10m"),
                "direction": self._format_wind_direction(current.get("wind_direction_10m", 0)),
                "unit": "km/h"
            },
            "weather": self._format_weather_code(current.get("weather_code", 0)),
            "time": current.get("time")
        }
        
        # Format hourly forecast (next 12 hours)
        forecast = []
        if hourly and "time" in hourly:
            times = hourly["time"][:12]
            temps = hourly.get("temperature_2m", [])[:12]
            precip_prob = hourly.get("precipitation_probability", [])[:12]
            precip = hourly.get("precipitation", [])[:12]
            weather_codes = hourly.get("weather_code", [])[:12]
            wind_speeds = hourly.get("wind_speed_10m", [])[:12]
            
            for i, time in enumerate(times):
                forecast.append({
                    "time": time,
                    "temperature": {
                        "value": temps[i] if i < len(temps) else None,
                        "unit": "°C"
                    },
                    "precipitation_probability": {
                        "value": precip_prob[i] if i < len(precip_prob) else None,
                        "unit": "%"
                    },
                    "precipitation": {
                        "value": precip[i] if i < len(precip) else None,
                        "unit": "mm"
                    },
                    "weather": self._format_weather_code(weather_codes[i]) if i < len(weather_codes) else "Unknown",
                    "wind_speed": {
                        "value": wind_speeds[i] if i < len(wind_speeds) else None,
                        "unit": "km/h"
                    }
                })
        
        return {
            "location": location_data["name"],
            "country": location_data.get("country", ""),
            "coordinates": {
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"]
            },
            "timezone": weather_data.get("timezone", "UTC"),
            "current_conditions": current_conditions,
            "hourly_forecast": forecast,
            "data_source": "Open-Meteo API (https://open-meteo.com)"
        }


# Initialize weather service
weather_service = WeatherService()


# MCP Tool Definition
@mcp.tool()
async def get_hourly_weather(location: str) -> Dict[str, Any]:
    """
    Get hourly weather forecast for a location using Open-Meteo API
    
    Args:
        location: City name (e.g., "Tallahassee", "New York", "London")
    
    Returns:
        Weather data including current conditions and 12-hour forecast with:
        - Temperature (Celsius)
        - Humidity
        - Precipitation and probability
        - Wind speed and direction
        - Weather conditions description
    """
    return await weather_service.get_weather(location)


# FastAPI Application
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Weather MCP Server",
        description="MCP server for weather data using Open-Meteo API (no API key required!)",
        version="2.0.0"
    )
    
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "Weather MCP Server",
            "version": "2.0.0",
            "api": "Open-Meteo (https://open-meteo.com)",
            "note": "No API key required!",
            "endpoints": {
                "health": "/health",
                "weather": "/weather?location=<city>",
                "docs": "/docs",
                "mcp": "/mcp/* (SSE endpoint)"
            }
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "mcp-weather",
            "api": "Open-Meteo",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/weather")
    async def get_weather_http(location: str):
        """
        Get weather for a location via HTTP GET
        
        Args:
            location: City name (query parameter)
            
        Example:
            GET /weather?location=Tallahassee
            GET /weather?location=London
            GET /weather?location=Tokyo
        """
        try:
            return await weather_service.get_weather(location)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Mount MCP SSE endpoint (deprecated warning is normal, still works fine)
    app.mount("/mcp", mcp.sse_app())
    
    return app


# Create app instance
app = create_app()


def main():
    """Main entry point"""
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    if transport == "http":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "3000"))
        
        logger.info(f"Starting Weather MCP Server in HTTP mode")
        logger.info(f"Using Open-Meteo API (no API key required)")
        logger.info(f"Listening on http://{host}:{port}")
        logger.info(f"API docs available at http://{host}:{port}/docs")
        
        # Print registered routes
        print("\n" + "="*50)
        print("📋 Registered Routes:")
        print("="*50)
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ', '.join(route.methods)
                print(f"  {methods:8} {route.path}")
            elif hasattr(route, 'path'):
                print(f"  MOUNT    {route.path} -> MCP SSE")
        print("="*50 + "\n")
        
        uvicorn.run(app, host=host, port=port, log_level="info")
    else:
        logger.info("Starting Weather MCP Server in stdio mode")
        logger.info("Using Open-Meteo API (no API key required)")
        mcp.run()


if __name__ == "__main__":
    main()