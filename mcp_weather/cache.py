"""
Location caching system for Weather MCP Server

Provides persistent caching of geocoded location coordinates to reduce API calls.
Uses JSON file storage with expiry mechanism.

Enhanced Features:
- Smart city-country parsing (e.g., "Paris, France" vs "Paris, TX")
- State/province handling (e.g., "Cleveland, GA" vs "Cleveland, OH")
- Handling of special characters in location names
- Prevention of cache collisions between similarly named cities
"""

import json
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from mcp_weather.config import CacheConfig

logger = logging.getLogger(__name__)


class LocationData:
    """
    Represents cached location data with coordinates and metadata
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
                logger.warning(f"Invalid cached_at timestamp: {data.get('cached_at')}")
                cached_at = datetime.now()
        
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"],
            name=data["name"],
            country=data.get("country", ""),
            timezone=data.get("timezone", "auto"),
            cached_at=cached_at
        )
    
    def is_expired(self, expiry_days: int) -> bool:
        """Check if cached data has expired"""
        age = datetime.now() - self.cached_at
        return age > timedelta(days=expiry_days)


class LocationCache:
    """
    Manages persistent caching of location coordinates with expiry
    
    Features:
        - JSON file storage in user's cache directory
        - 30-day default expiry (configurable)
        - Case-insensitive location lookup
        - Atomic file operations for data safety
        - Automatic cache directory creation
        - Graceful error handling for corrupted cache files
        - Enhanced location handling for "City, Country" and "City, State, Country" formats
        - Support for U.S. state abbreviations
    
    Thread Safety:
        - Not thread-safe by default
        - File operations use atomic rename for write safety
        - Consider adding file locking for multi-process scenarios
    """
    
    # US state abbreviations for reference
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
    
    def __init__(self, config: CacheConfig):
        """
        Initialize location cache
        
        Args:
            config: Cache configuration object
        """
        self.config = config
        self.cache_file = config.location_cache_file
        self.expiry_days = config.expiry_days
        
        # Ensure cache directory exists
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist"""
        try:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory ready: {self.config.cache_dir}")
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
    
    def _normalize_key(self, location: str) -> str:
        """
        Normalize location name for consistent cache lookups
        
        Handles various formats:
        - "Vancouver, Canada" -> "vancouver_canada"
        - "New York City, NY, USA" -> "newyorkcity_ny_usa"
        
        Args:
            location: Location name to normalize
            
        Returns:
            Normalized location key
        """
        # Strip and lowercase
        key = location.strip().lower()
        
        # Replace commas and multiple spaces with underscores
        key = re.sub(r'[,\s]+', '_', key)
        
        # Remove any trailing or duplicate underscores
        key = re.sub(r'_+', '_', key)
        key = re.sub(r'_$', '', key)
        
        # Log for debugging
        logger.debug(f"Normalized cache key: '{location}' -> '{key}'")
        
        return key
        
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
            else:
                country = second_part
                
        elif len(parts) >= 3:
            # Format: "City, State, Country"
            state = parts[1]
            country = parts[2]
            
            # If we have more than 3 parts, combine the rest into the country
            if len(parts) > 3:
                country = ", ".join(parts[2:])
        
        return city, state, country
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """
        Load cache from disk
        
        Returns:
            Dictionary of cached location data, empty dict if file doesn't exist or is corrupted
        """
        if not self.cache_file.exists():
            logger.debug(f"Cache file does not exist: {self.cache_file}")
            return {}
        
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                logger.debug(f"Loaded cache with {len(cache)} entries")
                return cache
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted cache file, starting fresh: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to read cache file: {e}")
            return {}
    
    def _save_cache(self, cache: Dict[str, Dict[str, Any]]) -> None:
        """
        Save cache to disk using atomic write operation
        
        Args:
            cache: Dictionary of location data to save
        """
        try:
            # Write to temporary file first (atomic operation)
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            
            # Atomic rename (replaces old file)
            temp_file.replace(self.cache_file)
            logger.debug(f"Saved cache with {len(cache)} entries")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
    
    def get(self, location: str) -> Optional[LocationData]:
        """
        Get cached location data if it exists and hasn't expired
        
        For locations with "City, Country" format or "City, State, Country" format:
        - Only return exact matches for the full normalized key
        - DO NOT return city-only matches (we want exact state/country matching)
        
        For city-only locations:
        - Return city matches as normal
        
        Args:
            location: Location name to look up
            
        Returns:
            LocationData if found and valid, None otherwise
        """
        # Parse location components
        city, state, country = self._parse_location(location)
        
        # For locations with state or country, we need exact matching
        if state or country:
            logger.info(f"Looking for exact cache match for '{location}' with state or country")
            cache_key = self._normalize_key(location)
            cache = self._load_cache()
            
            entry_dict = cache.get(cache_key)
            if not entry_dict:
                # Don't fall back to city-only for locations with state or country
                # This prevents Santiago, Chile from using cached Santiago, Dominican Republic
                # And prevents Cleveland, GA from using Cleveland, OH
                logger.debug(f"No exact cache match for '{location}' - not using city-only fallback")
                return None
            
            try:
                # Parse cached entry
                location_data = LocationData.from_dict(entry_dict)
                
                # Check expiry
                if location_data.is_expired(self.expiry_days):
                    logger.info(f"Cache expired for: {location} (age: {datetime.now() - location_data.cached_at})")
                    return None
                
                logger.info(f"Found exact cache match for '{location}'")
                return location_data
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Invalid cache entry for {location}: {e}")
                return None
        
        # For city-only format, try exact match
        logger.info(f"Looking for cache match for city-only location '{location}'")
        cache_key = self._normalize_key(location)
        cache = self._load_cache()
        
        entry_dict = cache.get(cache_key)
        if not entry_dict:
            logger.debug(f"Cache miss for: {location}")
            return None
        
        try:
            # Parse cached entry
            location_data = LocationData.from_dict(entry_dict)
            
            # Check expiry
            if location_data.is_expired(self.expiry_days):
                logger.info(f"Cache expired for: {location} (age: {datetime.now() - location_data.cached_at})")
                return None
            
            logger.info(f"Cache hit for: {location}")
            return location_data
            
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Invalid cache entry for {location}: {e}")
            return None
    
    def set(self, location: str, data: LocationData) -> None:
        """
        Cache location data with current timestamp
        
        Args:
            location: Location name (will be normalized)
            data: LocationData to cache
        """
        cache_key = self._normalize_key(location)
        cache = self._load_cache()
        
        # Update timestamp
        data.cached_at = datetime.now()
        
        # Store in cache
        cache[cache_key] = data.to_dict()
        self._save_cache(cache)
        
        logger.info(f"Cached location data for: {location}")
    
    def invalidate(self, location: str) -> bool:
        """
        Remove a specific location from cache
        
        Args:
            location: Location name to remove
            
        Returns:
            True if entry was removed, False if not found
        """
        cache_key = self._normalize_key(location)
        cache = self._load_cache()
        
        if cache_key in cache:
            del cache[cache_key]
            self._save_cache(cache)
            logger.info(f"Invalidated cache for: {location}")
            return True
        
        return False
    
    def clear(self) -> int:
        """
        Clear all cached data
        
        Returns:
            Number of entries that were cleared
        """
        cache = self._load_cache()
        count = len(cache)
        
        if count > 0:
            self._save_cache({})
            logger.info(f"Cleared {count} cache entries")
        
        return count
    
    def clean_expired(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of entries that were removed
        """
        cache = self._load_cache()
        original_count = len(cache)
        
        # Filter out expired entries
        cleaned_cache = {}
        for key, entry_dict in cache.items():
            try:
                location_data = LocationData.from_dict(entry_dict)
                if not location_data.is_expired(self.expiry_days):
                    cleaned_cache[key] = entry_dict
            except Exception as e:
                logger.warning(f"Removing invalid entry {key}: {e}")
        
        removed_count = original_count - len(cleaned_cache)
        
        if removed_count > 0:
            self._save_cache(cleaned_cache)
            logger.info(f"Cleaned {removed_count} expired/invalid entries")
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        cache = self._load_cache()
        
        expired_count = 0
        for entry_dict in cache.values():
            try:
                location_data = LocationData.from_dict(entry_dict)
                if location_data.is_expired(self.expiry_days):
                    expired_count += 1
            except Exception:
                expired_count += 1
        
        return {
            "total_entries": len(cache),
            "expired_entries": expired_count,
            "valid_entries": len(cache) - expired_count,
            "cache_file": str(self.cache_file),
            "expiry_days": self.expiry_days
        }