import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
import logging

class CacheManager:
    """
    Enhanced cache manager for URL processing data with individual URL support.
    Provides URL-aware caching with partial cache hits and configurable expiration.
    """
    
    def __init__(self, cache_dir: str = "cache", default_ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.default_ttl_hours = default_ttl_hours
        self.cache_index_file = os.path.join(cache_dir, "cache_index.json")
        self.url_index_file = os.path.join(cache_dir, "url_index.json")
        self.logger = logging.getLogger(__name__)
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load cache indices
        self.cache_index = self._load_cache_index()
        self.url_index = self._load_url_index()
    
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
    
    def _load_url_index(self) -> Dict:
        """Load the URL index file that tracks individual URL caching."""
        if os.path.exists(self.url_index_file):
            try:
                with open(self.url_index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load URL index: {e}. Starting with empty index.")
        return {
            "url_entries": {},
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
    
    def _save_url_index(self):
        """Save the URL index to disk."""
        try:
            with open(self.url_index_file, 'w') as f:
                json.dump(self.url_index, f, indent=2)
        except IOError as e:
            self.logger.error(f"Failed to save URL index: {e}")
    
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
    
    def _generate_url_cache_key(self, url: str, levels: List[int]) -> str:
        """Generate a cache key for individual URL data."""
        sorted_levels = sorted(levels)
        cache_data = {
            "url": url,
            "levels": sorted_levels
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    def _get_cache_entry_path(self, cache_key: str) -> str:
        """Get the file path for a cache entry."""
        return os.path.join(self.cache_dir, f"data_{cache_key}.json")
    
    def _get_cache_metadata_path(self, cache_key: str) -> str:
        """Get the file path for cache metadata."""
        return os.path.join(self.cache_dir, f"meta_{cache_key}.json")
    
    def _get_url_cache_entry_path(self, url_cache_key: str) -> str:
        """Get the file path for individual URL cache entry."""
        return os.path.join(self.cache_dir, f"url_data_{url_cache_key}.json")
    
    def _get_url_cache_metadata_path(self, url_cache_key: str) -> str:
        """Get the file path for individual URL cache metadata."""
        return os.path.join(self.cache_dir, f"url_meta_{url_cache_key}.json")

    def check_individual_url_cache(self, urls: List[str], levels: List[int], 
                                 custom_ttl_hours: Optional[int] = None) -> Tuple[Dict[str, any], List[str]]:
        """
        Check which individual URLs are cached and which need processing.
        
        Returns:
            Tuple[Dict[str, any], List[str]]: (cached_url_data, urls_to_process)
        """
        ttl_hours = custom_ttl_hours or self.default_ttl_hours
        cutoff_time = datetime.now() - timedelta(hours=ttl_hours)
        
        cached_url_data = {}
        urls_to_process = []
        
        for url in urls:
            url_cache_key = self._generate_url_cache_key(url, levels)
            
            # Check if URL is cached
            if url_cache_key in self.url_index["url_entries"]:
                entry = self.url_index["url_entries"][url_cache_key]
                cache_file = self._get_url_cache_entry_path(url_cache_key)
                metadata_file = self._get_url_cache_metadata_path(url_cache_key)
                
                # Check if files exist and cache is not expired
                if (os.path.exists(cache_file) and os.path.exists(metadata_file)):
                    created_time = datetime.fromisoformat(entry["created_at"])
                    
                    if created_time > cutoff_time:
                        # Cache hit - load cached data
                        try:
                            with open(cache_file, 'r') as f:
                                url_data = json.load(f)
                            
                            # Validate that cached data actually contains data for this URL
                            # Check if any entry in url_data has the matching URL
                            has_valid_data = False
                            for guid, guid_data in url_data.items():
                                if guid_data.get('url') == url and guid_data.get('html_data'):
                                    has_valid_data = True
                                    break
                            
                            if has_valid_data:
                                # Merge cached data for this URL
                                cached_url_data.update(url_data)
                                self.logger.info(f"✅ Cache hit for URL: {url} (key: {url_cache_key[:8]}...)")
                                
                                # Update access time
                                entry["last_accessed"] = datetime.now().isoformat()
                                continue
                            else:
                                # Cache file exists but doesn't contain valid data for this URL
                                self.logger.warning(f"⚠️  Cache file exists for URL: {url} but contains no valid data - will reprocess")
                                # Remove invalid cache entry
                                self._remove_url_cache_entry(url_cache_key)
                            
                        except (json.JSONDecodeError, IOError) as e:
                            self.logger.error(f"Failed to load cached URL data: {e}")
                            # Remove corrupted cache entry
                            self._remove_url_cache_entry(url_cache_key)
                    else:
                        self.logger.info(f"⏰ Cache expired for URL: {url}")
                else:
                    self.logger.warning(f"🗂️ Cache files missing for URL: {url}")
            
            # No valid cache - add to processing list
            urls_to_process.append(url)
            self.logger.info(f"❌ Cache miss for URL: {url}")
        
        # Save updated access times
        if cached_url_data:
            self._save_url_index()
        
        return cached_url_data, urls_to_process

    def has_valid_cache(self, urls: List[str], levels: List[int], 
                       custom_ttl_hours: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if valid cached data exists for the given URLs and levels.
        Now also checks for partial cache hits.
        
        Returns:
            Tuple[bool, Optional[str]]: (has_complete_cache, cache_key)
        """
        cache_key = self._generate_cache_key(urls, levels)
        
        # First check for complete cache (all URLs together)
        if cache_key in self.cache_index["entries"]:
            entry = self.cache_index["entries"][cache_key]
            cache_file = self._get_cache_entry_path(cache_key)
            metadata_file = self._get_cache_metadata_path(cache_key)
            
            # Check if files still exist
            if os.path.exists(cache_file) and os.path.exists(metadata_file):
                # Check expiration
                ttl_hours = custom_ttl_hours or self.default_ttl_hours
                created_time = datetime.fromisoformat(entry["created_at"])
                expiry_time = created_time + timedelta(hours=ttl_hours)
                
                if datetime.now() <= expiry_time:
                    # Validate data integrity
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        # Verify URLs and levels match in metadata
                        if (set(metadata["urls"]) == set(urls) and 
                            set(metadata["levels"]) == set(levels)):
                            # CRITICAL: Also verify that cached data actually contains entries for all URLs
                            try:
                                with open(cache_file, 'r') as f:
                                    cached_data = json.load(f)
                                
                                # Extract URLs from cached data
                                cached_urls_in_data = set()
                                for guid, guid_data in cached_data.items():
                                    url = guid_data.get('url')
                                    if url:
                                        cached_urls_in_data.add(url)
                                
                                # Check if all requested URLs are present in cached data
                                requested_urls_set = set(urls)
                                missing_urls = requested_urls_set - cached_urls_in_data
                                
                                if missing_urls:
                                    self.logger.warning(f"⚠️  Complete cache found but missing data for {len(missing_urls)} URLs: {missing_urls}")
                                    # Don't treat as complete cache if data is incomplete
                                    return False, cache_key
                                
                                # All URLs present - valid complete cache
                                return True, cache_key
                                
                            except (json.JSONDecodeError, IOError) as e:
                                self.logger.error(f"Failed to validate cached data: {e}")
                                return False, cache_key
                            
                    except (json.JSONDecodeError, IOError, KeyError) as e:
                        self.logger.error(f"Failed to validate cache metadata: {e}")
                        return False, cache_key
        
        # Check for partial cache hits
        cached_url_data, urls_to_process = self.check_individual_url_cache(urls, levels, custom_ttl_hours)
        
        if cached_url_data and len(urls_to_process) < len(urls):
            self.logger.info(f"🔍 Partial cache hit: {len(urls) - len(urls_to_process)}/{len(urls)} URLs cached")
            return False, cache_key  # Still return False for complete cache, but partial data is available
        
        return False, cache_key
    
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
    
    def get_partial_cached_data(self, urls: List[str], levels: List[int], 
                              custom_ttl_hours: Optional[int] = None) -> Tuple[Dict, List[str]]:
        """
        Get partial cached data and list of URLs that need processing.
        
        Returns:
            Tuple[Dict, List[str]]: (merged_cached_data, urls_to_process)
        """
        return self.check_individual_url_cache(urls, levels, custom_ttl_hours)

    def save_to_cache(self, urls: List[str], levels: List[int], data: Dict, 
                     processing_time: float = 0) -> str:
        """
        Save processing results to cache (both complete and individual URL caches).
        
        Args:
            urls: List of processed URLs
            levels: List of processed levels
            data: The data to cache
            processing_time: Time taken to process (for statistics)
            
        Returns:
            str: The cache key used
        """
        cache_key = self._generate_cache_key(urls, levels)
        
        # Save complete cache entry
        self._save_complete_cache_entry(cache_key, urls, levels, data, processing_time)
        
        # Save individual URL cache entries
        self._save_individual_url_cache_entries(urls, levels, data, processing_time)
        
        return cache_key
    
    def _save_complete_cache_entry(self, cache_key: str, urls: List[str], levels: List[int], 
                                 data: Dict, processing_time: float):
        """Save the complete cache entry."""
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
            self.logger.info(f"💾 Complete cache saved with key: {cache_key[:8]}...")
            
        except IOError as e:
            self.logger.error(f"Failed to save complete cache: {e}")
    
    def _save_individual_url_cache_entries(self, urls: List[str], levels: List[int], 
                                         data: Dict, processing_time: float):
        """Save individual URL cache entries."""
        for url in urls:
            url_cache_key = self._generate_url_cache_key(url, levels)
            
            # Extract data for this specific URL
            url_specific_data = {guid: guid_data for guid, guid_data in data.items() 
                               if guid_data.get('url') == url}
            
            if not url_specific_data:
                self.logger.warning(f"No data found for URL: {url}")
                continue
            
            cache_file = self._get_url_cache_entry_path(url_cache_key)
            metadata_file = self._get_url_cache_metadata_path(url_cache_key)
            
            try:
                # Save URL-specific data
                with open(cache_file, 'w') as f:
                    json.dump(url_specific_data, f, indent=2)
                
                # Save URL metadata
                metadata = {
                    "url": url,
                    "levels": levels,
                    "cache_key": url_cache_key,
                    "created_at": datetime.now().isoformat(),
                    "processing_time": processing_time / len(urls),  # Approximate time per URL
                    "data_size_bytes": os.path.getsize(cache_file),
                    "num_records": len(url_specific_data)
                }
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Update URL index
                self.url_index["url_entries"][url_cache_key] = {
                    "url": url,
                    "levels": levels,
                    "created_at": metadata["created_at"],
                    "last_accessed": metadata["created_at"],
                    "file_size_bytes": metadata["data_size_bytes"],
                    "processing_time": metadata["processing_time"],
                    "num_records": metadata["num_records"]
                }
                
                self.logger.info(f"🔗 Individual URL cached: {url} (key: {url_cache_key[:8]}...)")
                
            except IOError as e:
                self.logger.error(f"Failed to save URL cache for {url}: {e}")
        
        # Save URL index
        self._save_url_index()

    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache."""
        complete_entries = len(self.cache_index["entries"])
        url_entries = len(self.url_index["url_entries"])
        
        total_size = sum(entry.get("file_size_bytes", 0) 
                        for entry in self.cache_index["entries"].values())
        url_size = sum(entry.get("file_size_bytes", 0) 
                      for entry in self.url_index["url_entries"].values())
        
        if complete_entries == 0 and url_entries == 0:
            return {
                "total_entries": 0,
                "complete_cache_entries": 0,
                "individual_url_entries": 0,
                "total_size_mb": 0,
                "average_processing_time": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "cache_efficiency": "No data"
            }
        
        # Calculate statistics
        all_processing_times = []
        all_created_times = []
        
        for entry in self.cache_index["entries"].values():
            all_processing_times.append(entry.get("processing_time", 0))
            all_created_times.append(datetime.fromisoformat(entry["created_at"]))
        
        for entry in self.url_index["url_entries"].values():
            all_processing_times.append(entry.get("processing_time", 0))
            all_created_times.append(datetime.fromisoformat(entry["created_at"]))
        
        return {
            "total_entries": complete_entries + url_entries,
            "complete_cache_entries": complete_entries,
            "individual_url_entries": url_entries,
            "total_size_mb": (total_size + url_size) / (1024 * 1024),
            "complete_cache_size_mb": total_size / (1024 * 1024),
            "url_cache_size_mb": url_size / (1024 * 1024),
            "average_processing_time": sum(all_processing_times) / len(all_processing_times) if all_processing_times else 0,
            "oldest_entry": min(all_created_times).isoformat() if all_created_times else None,
            "newest_entry": max(all_created_times).isoformat() if all_created_times else None,
            "cache_efficiency": f"{url_entries} individual URLs cached for reuse"
        }

    def cleanup_expired(self, ttl_hours: Optional[int] = None) -> int:
        """
        Remove expired cache entries (both complete and individual URL caches).
        
        Returns:
            int: Number of entries removed
        """
        ttl_hours = ttl_hours or self.default_ttl_hours
        cutoff_time = datetime.now() - timedelta(hours=ttl_hours)
        
        # Clean up complete cache entries
        expired_keys = []
        for cache_key, entry in self.cache_index["entries"].items():
            created_time = datetime.fromisoformat(entry["created_at"])
            if created_time < cutoff_time:
                expired_keys.append(cache_key)
        
        # Clean up URL cache entries
        expired_url_keys = []
        for url_cache_key, entry in self.url_index["url_entries"].items():
            created_time = datetime.fromisoformat(entry["created_at"])
            if created_time < cutoff_time:
                expired_url_keys.append(url_cache_key)
        
        # Remove expired entries
        removed_count = 0
        for cache_key in expired_keys:
            if self._remove_cache_entry(cache_key):
                removed_count += 1
        
        for url_cache_key in expired_url_keys:
            if self._remove_url_cache_entry(url_cache_key):
                removed_count += 1
        
        if removed_count > 0:
            self.cache_index["last_cleanup"] = datetime.now().isoformat()
            self.url_index["last_cleanup"] = datetime.now().isoformat()
            self._save_cache_index()
            self._save_url_index()
            self.logger.info(f"🧹 Removed {removed_count} expired cache entries")
        
        return removed_count
    
    def _remove_cache_entry(self, cache_key: str) -> bool:
        """Remove a single complete cache entry and its files."""
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
    
    def _remove_url_cache_entry(self, url_cache_key: str) -> bool:
        """Remove a single URL cache entry and its files."""
        try:
            # Remove files
            cache_file = self._get_url_cache_entry_path(url_cache_key)
            metadata_file = self._get_url_cache_metadata_path(url_cache_key)
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            # Remove from index
            if url_cache_key in self.url_index["url_entries"]:
                del self.url_index["url_entries"][url_cache_key]
            
            return True
            
        except OSError as e:
            self.logger.error(f"Failed to remove URL cache entry {url_cache_key}: {e}")
            return False

    def clear_all_cache(self) -> int:
        """
        Clear all cached data (both complete and individual URL caches).
        
        Returns:
            int: Number of entries removed
        """
        complete_keys = list(self.cache_index["entries"].keys())
        url_keys = list(self.url_index["url_entries"].keys())
        
        removed_count = 0
        
        # Remove complete cache entries
        for cache_key in complete_keys:
            if self._remove_cache_entry(cache_key):
                removed_count += 1
        
        # Remove URL cache entries
        for url_cache_key in url_keys:
            if self._remove_url_cache_entry(url_cache_key):
                removed_count += 1
        
        # Reset indices
        self.cache_index = {
            "entries": {},
            "created_at": datetime.now().isoformat(),
            "last_cleanup": datetime.now().isoformat()
        }
        self.url_index = {
            "url_entries": {},
            "created_at": datetime.now().isoformat(),
            "last_cleanup": datetime.now().isoformat()
        }
        
        self._save_cache_index()
        self._save_url_index()
        
        self.logger.info(f"🗑️ Cleared all cache: {removed_count} entries removed")
        return removed_count

    def list_cache_entries(self) -> List[Dict]:
        """Get a list of all cache entries with their metadata."""
        entries = []
        
        # Add complete cache entries
        for cache_key, entry in self.cache_index["entries"].items():
            entry_info = entry.copy()
            entry_info["cache_key"] = cache_key
            entry_info["cache_type"] = "complete"
            entry_info["age_hours"] = (
                datetime.now() - datetime.fromisoformat(entry["created_at"])
            ).total_seconds() / 3600
            entries.append(entry_info)
        
        # Add individual URL cache entries
        for url_cache_key, entry in self.url_index["url_entries"].items():
            entry_info = entry.copy()
            entry_info["cache_key"] = url_cache_key
            entry_info["cache_type"] = "individual_url"
            entry_info["age_hours"] = (
                datetime.now() - datetime.fromisoformat(entry["created_at"])
            ).total_seconds() / 3600
            entries.append(entry_info)
        
        # Sort by creation time (newest first)
        entries.sort(key=lambda x: x["created_at"], reverse=True)
        return entries 