import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

class CacheManager:
    """
    Enhanced cache manager for URL processing data.
    Provides URL-aware caching with configurable expiration and validation.
    """
    
    def __init__(self, cache_dir: str = "cache", default_ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.default_ttl_hours = default_ttl_hours
        self.cache_index_file = os.path.join(cache_dir, "cache_index.json")
        self.logger = logging.getLogger(__name__)
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load cache index
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict:
        """Load the cache index file that tracks all cached entries."""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load cache index: {e}. Starting with empty index.")
        return {
            "entries": {},
            "created_at": datetime.now().isoformat(),
            "last_cleanup": datetime.now().isoformat()
        }
    
    def _save_cache_index(self):
        """Save the cache index to disk."""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except IOError as e:
            self.logger.error(f"Failed to save cache index: {e}")
    
    def _generate_cache_key(self, urls: List[str], levels: List[int]) -> str:
        """Generate a unique cache key based on URLs and levels."""
        # Sort URLs and levels for consistent hashing
        sorted_urls = sorted(urls)
        sorted_levels = sorted(levels)
        
        # Create a unique string representation
        cache_data = {
            "urls": sorted_urls,
            "levels": sorted_levels
        }
        
        # Generate SHA256 hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    def _get_cache_entry_path(self, cache_key: str) -> str:
        """Get the file path for a cache entry."""
        return os.path.join(self.cache_dir, f"data_{cache_key}.json")
    
    def _get_cache_metadata_path(self, cache_key: str) -> str:
        """Get the file path for cache metadata."""
        return os.path.join(self.cache_dir, f"meta_{cache_key}.json")
    
    def has_valid_cache(self, urls: List[str], levels: List[int], 
                       custom_ttl_hours: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if valid cached data exists for the given URLs and levels.
        
        Returns:
            Tuple[bool, Optional[str]]: (has_valid_cache, cache_key)
        """
        cache_key = self._generate_cache_key(urls, levels)
        
        # Check if entry exists in index
        if cache_key not in self.cache_index["entries"]:
            return False, cache_key
        
        entry = self.cache_index["entries"][cache_key]
        cache_file = self._get_cache_entry_path(cache_key)
        metadata_file = self._get_cache_metadata_path(cache_key)
        
        # Check if files still exist
        if not os.path.exists(cache_file) or not os.path.exists(metadata_file):
            self.logger.warning(f"Cache files missing for key {cache_key}, removing from index")
            del self.cache_index["entries"][cache_key]
            self._save_cache_index()
            return False, cache_key
        
        # Check expiration
        ttl_hours = custom_ttl_hours or self.default_ttl_hours
        created_time = datetime.fromisoformat(entry["created_at"])
        expiry_time = created_time + timedelta(hours=ttl_hours)
        
        if datetime.now() > expiry_time:
            self.logger.info(f"Cache expired for key {cache_key}")
            return False, cache_key
        
        # Validate data integrity
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Verify URLs and levels match
            if (set(metadata["urls"]) != set(urls) or 
                set(metadata["levels"]) != set(levels)):
                self.logger.warning(f"Cache content mismatch for key {cache_key}")
                return False, cache_key
                
        except (json.JSONDecodeError, IOError, KeyError) as e:
            self.logger.error(f"Failed to validate cache metadata: {e}")
            return False, cache_key
        
        return True, cache_key
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached data by cache key."""
        cache_file = self._get_cache_entry_path(cache_key)
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Update access time
            if cache_key in self.cache_index["entries"]:
                self.cache_index["entries"][cache_key]["last_accessed"] = datetime.now().isoformat()
                self._save_cache_index()
            
            return data
            
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load cached data: {e}")
            return None
    
    def save_to_cache(self, urls: List[str], levels: List[int], data: Dict, 
                     processing_time: float = 0) -> str:
        """
        Save processing results to cache.
        
        Args:
            urls: List of processed URLs
            levels: List of processed levels
            data: The data to cache
            processing_time: Time taken to process (for statistics)
            
        Returns:
            str: The cache key used
        """
        cache_key = self._generate_cache_key(urls, levels)
        cache_file = self._get_cache_entry_path(cache_key)
        metadata_file = self._get_cache_metadata_path(cache_key)
        
        try:
            # Save the actual data
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Save metadata
            metadata = {
                "urls": urls,
                "levels": levels,
                "cache_key": cache_key,
                "created_at": datetime.now().isoformat(),
                "processing_time": processing_time,
                "data_size_bytes": os.path.getsize(cache_file),
                "num_records": len(data) if isinstance(data, dict) else 0
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update cache index
            self.cache_index["entries"][cache_key] = {
                "urls": urls,
                "levels": levels,
                "created_at": metadata["created_at"],
                "last_accessed": metadata["created_at"],
                "file_size_bytes": metadata["data_size_bytes"],
                "processing_time": processing_time,
                "num_records": metadata["num_records"]
            }
            
            self._save_cache_index()
            
            self.logger.info(f"Data cached successfully with key: {cache_key}")
            return cache_key
            
        except IOError as e:
            self.logger.error(f"Failed to save to cache: {e}")
            return cache_key
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache."""
        total_entries = len(self.cache_index["entries"])
        total_size = sum(entry.get("file_size_bytes", 0) 
                        for entry in self.cache_index["entries"].values())
        
        if total_entries == 0:
            return {
                "total_entries": 0,
                "total_size_mb": 0,
                "average_processing_time": 0,
                "oldest_entry": None,
                "newest_entry": None
            }
        
        processing_times = [entry.get("processing_time", 0) 
                          for entry in self.cache_index["entries"].values()]
        created_times = [datetime.fromisoformat(entry["created_at"]) 
                        for entry in self.cache_index["entries"].values()]
        
        return {
            "total_entries": total_entries,
            "total_size_mb": total_size / (1024 * 1024),
            "average_processing_time": sum(processing_times) / len(processing_times),
            "oldest_entry": min(created_times).isoformat(),
            "newest_entry": max(created_times).isoformat()
        }
    
    def cleanup_expired(self, ttl_hours: Optional[int] = None) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            int: Number of entries removed
        """
        ttl_hours = ttl_hours or self.default_ttl_hours
        cutoff_time = datetime.now() - timedelta(hours=ttl_hours)
        
        expired_keys = []
        for cache_key, entry in self.cache_index["entries"].items():
            created_time = datetime.fromisoformat(entry["created_at"])
            if created_time < cutoff_time:
                expired_keys.append(cache_key)
        
        # Remove expired entries
        removed_count = 0
        for cache_key in expired_keys:
            if self._remove_cache_entry(cache_key):
                removed_count += 1
        
        if removed_count > 0:
            self.cache_index["last_cleanup"] = datetime.now().isoformat()
            self._save_cache_index()
            self.logger.info(f"Removed {removed_count} expired cache entries")
        
        return removed_count
    
    def _remove_cache_entry(self, cache_key: str) -> bool:
        """Remove a single cache entry and its files."""
        try:
            # Remove files
            cache_file = self._get_cache_entry_path(cache_key)
            metadata_file = self._get_cache_metadata_path(cache_key)
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            # Remove from index
            if cache_key in self.cache_index["entries"]:
                del self.cache_index["entries"][cache_key]
            
            return True
            
        except OSError as e:
            self.logger.error(f"Failed to remove cache entry {cache_key}: {e}")
            return False
    
    def clear_all_cache(self) -> int:
        """
        Clear all cached data.
        
        Returns:
            int: Number of entries removed
        """
        cache_keys = list(self.cache_index["entries"].keys())
        removed_count = 0
        
        for cache_key in cache_keys:
            if self._remove_cache_entry(cache_key):
                removed_count += 1
        
        self.cache_index = {
            "entries": {},
            "created_at": datetime.now().isoformat(),
            "last_cleanup": datetime.now().isoformat()
        }
        self._save_cache_index()
        
        self.logger.info(f"Cleared all cache: {removed_count} entries removed")
        return removed_count
    
    def list_cache_entries(self) -> List[Dict]:
        """Get a list of all cache entries with their metadata."""
        entries = []
        for cache_key, entry in self.cache_index["entries"].items():
            entry_info = entry.copy()
            entry_info["cache_key"] = cache_key
            entry_info["age_hours"] = (
                datetime.now() - datetime.fromisoformat(entry["created_at"])
            ).total_seconds() / 3600
            entries.append(entry_info)
        
        # Sort by creation time (newest first)
        entries.sort(key=lambda x: x["created_at"], reverse=True)
        return entries 