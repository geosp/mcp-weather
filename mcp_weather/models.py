"""
Pydantic models for Weather MCP Server

Defines request and response schemas for API endpoints and MCP tools.
Provides validation, serialization, and OpenAPI documentation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LocationData:
    """
    Represents location data with coordinates and metadata
    
    Used for geocoding results and caching.
    """
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        name: str,
        country: str = "",
        timezone: str = "auto",
        cached_at: Optional[datetime] = None
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.name = name
        self.country = country
        self.timezone = timezone
        self.cached_at = cached_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "name": self.name,
            "country": self.country,
            "timezone": self.timezone,
            "cached_at": self.cached_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocationData":
        """Create from dictionary (JSON deserialization)"""
        cached_at = None
        if "cached_at" in data:
            try:
                cached_at = datetime.fromisoformat(data["cached_at"])
            except (ValueError, TypeError):
                cached_at = datetime.now()
        
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"],
            name=data["name"],
            country=data.get("country", ""),
            timezone=data.get("timezone", "auto"),
            cached_at=cached_at
        )


# ============================================================================
# Request Models
# ============================================================================

class WeatherRequest(BaseModel):
    """Request model for weather data"""
    
    location: str = Field(
        ...,
        description="City name or location (e.g., 'Tallahassee', 'New York', 'London')",
        min_length=1,
        max_length=100,
        examples=["Tallahassee", "New York", "London", "Tokyo"]
    )
    
    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate and sanitize location input"""
        v = v.strip()
        if not v:
            raise ValueError("Location cannot be empty or only whitespace")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": "Tallahassee"
            }
        }
    )


class ForecastRequest(WeatherRequest):
    """Request model for extended forecast"""
    
    days: int = Field(
        default=1,
        ge=1,
        le=7,
        description="Number of forecast days (1-7)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": "Tallahassee",
                "days": 3
            }
        }
    )


# ============================================================================
# Response Models - Components
# ============================================================================

class Measurement(BaseModel):
    """Generic measurement with value and unit"""
    
    value: Optional[float] = Field(None, description="Measurement value")
    unit: str = Field(..., description="Unit of measurement")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": 22.5,
                "unit": "°C"
            }
        }
    )


class WindData(BaseModel):
    """Wind information"""
    
    speed: Optional[float] = Field(None, description="Wind speed")
    direction_degrees: Optional[float] = Field(None, description="Wind direction in degrees")
    direction: Optional[str] = Field(None, description="Cardinal direction (N, NE, E, etc.)")
    unit: str = Field(default="km/h", description="Speed unit")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "speed": 15.3,
                "direction_degrees": 245.0,
                "direction": "WSW",
                "unit": "km/h"
            }
        }
    )


class Coordinates(BaseModel):
    """Geographic coordinates"""
    
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 30.4383,
                "longitude": -84.2807
            }
        }
    )


class LocationInfo(BaseModel):
    """Location information"""
    
    name: str = Field(..., description="Location name")
    country: str = Field(default="", description="Country name")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    timezone: str = Field(default="UTC", description="Timezone identifier")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tallahassee",
                "country": "United States",
                "coordinates": {
                    "latitude": 30.4383,
                    "longitude": -84.2807
                },
                "timezone": "America/New_York"
            }
        }
    )


class CurrentConditions(BaseModel):
    """Current weather conditions"""
    
    temperature: Measurement = Field(..., description="Current temperature")
    feels_like: Measurement = Field(..., description="Apparent temperature")
    humidity: Measurement = Field(..., description="Relative humidity")
    precipitation: Measurement = Field(..., description="Current precipitation")
    wind: WindData = Field(..., description="Wind information")
    weather: str = Field(..., description="Weather description")
    time: str = Field(..., description="Observation time (ISO format)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "temperature": {"value": 22.5, "unit": "°C"},
                "feels_like": {"value": 21.8, "unit": "°C"},
                "humidity": {"value": 65, "unit": "%"},
                "precipitation": {"value": 0.0, "unit": "mm"},
                "wind": {
                    "speed": 15.3,
                    "direction_degrees": 245.0,
                    "direction": "WSW",
                    "unit": "km/h"
                },
                "weather": "Partly cloudy",
                "time": "2024-01-15T14:30:00"
            }
        }
    )


class HourlyForecast(BaseModel):
    """Hourly forecast data point"""
    
    time: str = Field(..., description="Forecast time (ISO format)")
    temperature: Measurement = Field(..., description="Temperature forecast")
    precipitation_probability: Measurement = Field(..., description="Chance of precipitation")
    precipitation: Measurement = Field(..., description="Expected precipitation amount")
    weather: str = Field(..., description="Weather description")
    wind_speed: Measurement = Field(..., description="Wind speed forecast")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time": "2024-01-15T15:00:00",
                "temperature": {"value": 23.0, "unit": "°C"},
                "precipitation_probability": {"value": 20, "unit": "%"},
                "precipitation": {"value": 0.1, "unit": "mm"},
                "weather": "Partly cloudy",
                "wind_speed": {"value": 12.5, "unit": "km/h"}
            }
        }
    )


# ============================================================================
# Main Response Models
# ============================================================================

class WeatherResponse(BaseModel):
    """Complete weather response"""
    
    location: str = Field(..., description="Location name")
    country: str = Field(default="", description="Country name")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    timezone: str = Field(default="UTC", description="Local timezone")
    current_conditions: CurrentConditions = Field(..., description="Current weather")
    hourly_forecast: List[HourlyForecast] = Field(..., description="Hourly forecast (next 12 hours)")
    data_source: str = Field(
        default="Open-Meteo API (https://open-meteo.com)",
        description="Weather data source attribution"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                        "direction_degrees": 245.0,
                        "direction": "WSW",
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
                ],
                "data_source": "Open-Meteo API (https://open-meteo.com)"
            }
        }
    )


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail information"""
    
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Location not found",
                "error_code": "LOCATION_NOT_FOUND",
                "details": {
                    "location": "Atlantis",
                    "suggestion": "Check spelling or try a different location"
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    
    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error information")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "message": "Location not found",
                    "error_code": "LOCATION_NOT_FOUND",
                    "details": {
                        "location": "Atlantis"
                    }
                },
                "timestamp": "2024-01-15T14:30:00Z"
            }
        }
    )


# ============================================================================
# Health and Info Response Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="mcp-weather", description="Service name")
    api: str = Field(default="Open-Meteo", description="Weather API provider")
    authentication: str = Field(default="Authentik enabled", description="Auth status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "service": "mcp-weather",
                "api": "Open-Meteo",
                "authentication": "Authentik enabled",
                "timestamp": "2024-01-15T14:30:00Z"
            }
        }
    )


class ServiceInfo(BaseModel):
    """Service information response"""
    
    name: str = Field(default="Weather MCP Server", description="Service name")
    version: str = Field(default="2.0.0", description="Service version")
    authentication: str = Field(..., description="Authentication method")
    api: str = Field(default="Open-Meteo (https://open-meteo.com)", description="Weather API")
    note: str = Field(
        default="No API key required for weather data!",
        description="Additional info"
    )
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Weather MCP Server",
                "version": "2.0.0",
                "authentication": "Authentik Bearer token required",
                "api": "Open-Meteo (https://open-meteo.com)",
                "note": "No API key required for weather data!",
                "endpoints": {
                    "health": "/health (no auth required)",
                    "weather": "/weather?location=<city> (requires auth)",
                    "docs": "/docs",
                    "mcp": "/mcp (MCP protocol - requires auth)"
                }
            }
        }
    )