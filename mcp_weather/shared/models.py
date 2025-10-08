"""
Shared models for Weather MCP Server

Defines common model components used across multiple features.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Common Components
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