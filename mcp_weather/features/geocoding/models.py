"""
Models for the geocoding feature
"""

from typing import Optional
from pydantic import BaseModel, Field


class GeocodingRequest(BaseModel):
    """
    Request model for geocoding a location
    """
    location: str = Field(..., 
                          description="Location to geocode (e.g., 'Paris', 'Toronto, Canada', 'Miami, FL')")


class GeocodingResponse(BaseModel):
    """
    Response model for geocoded location data
    """
    location: str = Field(..., description="Resolved location name")
    country: str = Field(..., description="Country where the location is situated")
    coordinates: dict = Field(..., description="Latitude and longitude coordinates")
    timezone: str = Field(..., description="Timezone identifier for the location")