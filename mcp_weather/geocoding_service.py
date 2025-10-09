"""
Geocoding service for resolving location names to coordinates

Handles parsing location strings, normalizing country and state/province names,
and converting location names to coordinates using Open-Meteo Geocoding API.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from aiohttp import ClientSession, ClientError, ClientTimeout
from fastapi import HTTPException

from core.cache import RedisCacheClient
from mcp_weather.models import LocationData

logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Handles geocoding operations using Open-Meteo Geocoding API
    
    This service provides location parsing and geocoding functionality:
    1. Parse location strings into components (city, state/province, country)
    2. Normalize country and state/province names
    3. Convert location names to coordinates via API
    4. Filter and prioritize results for accuracy
    
    Features:
        - Location string parsing and normalization
        - Support for various location formats
        - US state and Canadian province handling
        - Country name variation handling
        - Result filtering and prioritization
    """
    
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
    
    def __init__(self, geocoding_url: str, cache_client: RedisCacheClient):
        """
        Initialize geocoding service
        
        Args:
            geocoding_url: URL for the Open-Meteo Geocoding API
            cache_client: Redis cache client for storing geocoded coordinates
        """
        self.geocoding_url = geocoding_url
        self.cache_client = cache_client
        
        # HTTP client timeout configuration
        self.timeout = ClientTimeout(total=30, connect=10)
        
        logger.info(f"Initialized GeocodingService with geocoding URL: {self.geocoding_url}")
    
    def _parse_location(self, location: str) -> Tuple[str, Optional[str], Optional[str]]:
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

    async def geocode_location(self, session: ClientSession, location: str) -> LocationData:
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

    async def get_location_coordinates(self, session: ClientSession, location: str) -> LocationData:
        """
        Get coordinates for a location, using cache if available
        
        This is the main public method that should be called by consumers:
        1. Check if location is cached
        2. If not, geocode it and cache the result
        3. Return LocationData with coordinates
        
        Args:
            session: aiohttp client session
            location: Location name to geocode
            
        Returns:
            LocationData with coordinates and metadata
            
        Raises:
            ValueError: If location is invalid
            HTTPException: If geocoding fails
        """
        # Check cache for coordinates
        cached_location = await self.cache_client.get(location, LocationData.from_dict)
        
        if cached_location:
            logger.info(f"Using cached coordinates for {location}")
            return cached_location
        
        # Geocode the location
        logger.info(f"Cache miss, geocoding {location}")
        location_data = await self.geocode_location(session, location)
        
        # Cache the result as a dictionary
        await self.cache_client.set(location, location_data.to_dict())
        
        return location_data