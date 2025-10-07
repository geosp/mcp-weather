"""
Location caching system for Weather MCP Server

Provides persistent caching of geocoded location coordinates to reduce API calls.
Uses JSON file storage with expiry mechanism.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from .config import CacheConfig

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
    
    Thread Safety:
        - Not thread-safe by default
        - File operations use atomic rename for write safety
        - Consider adding file locking for multi-process scenarios
    """
    
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
        
        Args:
            location: Location name to normalize
            
        Returns:
            Normalized location key (lowercase, stripped)
        """
        return location.strip().lower()
    
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
        
        Args:
            location: Location name to look up
            
        Returns:
            LocationData if found and valid, None otherwise
        """
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