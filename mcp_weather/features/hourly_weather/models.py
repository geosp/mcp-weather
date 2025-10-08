"""
Models for the Hourly Weather feature

Defines request and response models for the hourly weather forecast feature.
"""

from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict

from mcp_weather.shared.models import Measurement, WindData, Coordinates


# ============================================================================
# Request Models
# ============================================================================

class WeatherRequest(BaseModel):
    """Request model for weather data"""
    
    location: str = Field(
        ...,
        description="City name or 'City, Country' format (e.g., 'Tallahassee', 'Vancouver, Canada')",
        min_length=1,
        max_length=100,
        examples=["Tallahassee", "New York", "London, UK", "Vancouver, Canada", "Tokyo, Japan"]
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
                "location": "Vancouver, Canada"
            }
        }
    )


# ============================================================================
# Response Models - Components
# ============================================================================

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
# Main Response Model
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