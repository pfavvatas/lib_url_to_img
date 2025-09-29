#!/usr/bin/env python3
"""
Test script to demonstrate the optimized cache system with partial cache hits.
This shows how individual URLs are cached and reused efficiently.
"""

import os
import sys
import time
import tempfile
import json
from datetime import datetime

# Add the lib directory to the path
sys.path.append(os.path.dirname(__file__))

from utils.cache_manager import CacheManager

def create_mock_url_data(urls, levels):
    """Create mock URL data for testing."""
    data = {}
    for i, url in enumerate(urls):
        for level in levels:
            guid = f"guid_{i}_{level}_{int(time.time() * 1000) % 10000}"
            data[guid] = {
                "url": url,
                "level": level,
                "html_data": {
                    "tag_name": "div",
                    "unique_id": guid,
                    "attributes": {"class": f"test-class-{level}"},
                    "children": []
                },
                "timestamp": datetime.now().isoformat()
            }
    return data

def test_cache_optimization():
    """Test the optimized cache system."""
    print("🚀 Testing Optimized Cache System\n")
    
    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_manager = CacheManager(cache_dir=temp_dir, default_ttl_hours=24)
        
        # Test URLs
        test_urls = [
            "https://example.com/page1",
            "https://example.com/page2", 
            "https://test.com/article1",
            "https://test.com/article2"
        ]
        levels = [1, 2]
        
        print("=" * 60)
        print("STEP 1: Initial processing - no cache")
        print("=" * 60)
        
        # Process first two URLs
        initial_urls = test_urls[:2]
        print(f"📝 Processing: {initial_urls}")
        
        # Check cache status
        has_complete, cache_key = cache_manager.has_valid_cache(initial_urls, levels)
        cached_data, urls_to_process = cache_manager.get_partial_cached_data(initial_urls, levels)
        
        print(f"🔍 Complete cache: {has_complete}")
        print(f"🔍 Partial cache: {len(cached_data)} items, URLs to process: {urls_to_process}")
        
        # Simulate processing
        mock_data = create_mock_url_data(initial_urls, levels)
        processing_time = 5.2  # Mock processing time
        
        saved_key = cache_manager.save_to_cache(initial_urls, levels, mock_data, processing_time)
        print(f"💾 Saved to cache with key: {saved_key[:8]}...")
        
        # Show cache stats
        stats = cache_manager.get_cache_stats()
        print(f"📊 Cache stats: {stats['complete_cache_entries']} complete + {stats['individual_url_entries']} individual entries")
        
        print("\n" + "=" * 60)
        print("STEP 2: Mixed processing - partial cache hit")
        print("=" * 60)
        
        # Process mix of old and new URLs
        mixed_urls = [test_urls[1], test_urls[2], test_urls[3]]  # One cached, two new
        print(f"📝 Processing: {mixed_urls}")
        
        # Check cache status
        has_complete, cache_key = cache_manager.has_valid_cache(mixed_urls, levels)
        cached_data, urls_to_process = cache_manager.get_partial_cached_data(mixed_urls, levels)
        
        print(f"🔍 Complete cache: {has_complete}")
        print(f"🔍 Partial cache: {len(cached_data)} items")
        print(f"🔍 URLs from cache: {[url for url in mixed_urls if url not in urls_to_process]}")
        print(f"🔍 URLs to process: {urls_to_process}")
        print(f"⚡ Cache efficiency: {((len(mixed_urls) - len(urls_to_process)) / len(mixed_urls) * 100):.1f}%")
        
        # Simulate processing only new URLs
        if urls_to_process:
            new_data = create_mock_url_data(urls_to_process, levels)
            # Merge with cached data
            complete_data = {**cached_data, **new_data}
            processing_time = len(urls_to_process) * 2.1  # Only processing new URLs
            
            saved_key = cache_manager.save_to_cache(mixed_urls, levels, complete_data, processing_time)
            print(f"💾 Saved complete set to cache with key: {saved_key[:8]}...")
            print(f"⏱️  Processing time: {processing_time:.1f}s (saved {(len(mixed_urls) - len(urls_to_process)) * 2.1:.1f}s from cache)")
        
        print("\n" + "=" * 60)
        print("STEP 3: Complete cache hit")
        print("=" * 60)
        
        # Request same URLs again
        print(f"📝 Processing: {mixed_urls}")
        
        # Check cache status
        has_complete, cache_key = cache_manager.has_valid_cache(mixed_urls, levels)
        cached_data, urls_to_process = cache_manager.get_partial_cached_data(mixed_urls, levels)
        
        print(f"🔍 Complete cache: {has_complete}")
        print(f"🔍 URLs to process: {urls_to_process}")
        
        if has_complete:
            complete_cached_data = cache_manager.get_cached_data(cache_key)
            print(f"✅ Loaded {len(complete_cached_data)} records from complete cache")
            print(f"⚡ Cache efficiency: 100% - No processing needed!")
        
        print("\n" + "=" * 60)
        print("STEP 4: All individual URLs cached")
        print("=" * 60)
        
        # Process all URLs - should all be in individual cache
        print(f"📝 Processing: {test_urls}")
        
        # Check cache status
        has_complete, cache_key = cache_manager.has_valid_cache(test_urls, levels)
        cached_data, urls_to_process = cache_manager.get_partial_cached_data(test_urls, levels)
        
        print(f"🔍 Complete cache: {has_complete}")
        print(f"🔍 Partial cache: {len(cached_data)} items")
        print(f"🔍 URLs to process: {urls_to_process}")
        print(f"⚡ Cache efficiency: {((len(test_urls) - len(urls_to_process)) / len(test_urls) * 100):.1f}%")
        
        if not urls_to_process:
            # All URLs cached individually - create complete cache entry
            saved_key = cache_manager.save_to_cache(test_urls, levels, cached_data, 0)
            print(f"💾 Created complete cache entry for this combination: {saved_key[:8]}...")
            print(f"✅ All URLs found in cache - no processing needed!")
        
        # Final cache stats
        final_stats = cache_manager.get_cache_stats()
        print(f"\n📊 Final cache stats:")
        print(f"   • Total entries: {final_stats['total_entries']}")
        print(f"   • Complete cache entries: {final_stats['complete_cache_entries']}")
        print(f"   • Individual URL entries: {final_stats['individual_url_entries']}")
        print(f"   • Total size: {final_stats['total_size_mb']:.2f} MB")
        print(f"   • Cache efficiency: {final_stats['cache_efficiency']}")
        
        print("\n🎉 Cache optimization test completed successfully!")
        
        # Test cache entry listing
        print("\n" + "=" * 60)
        print("CACHE ENTRIES")
        print("=" * 60)
        
        entries = cache_manager.list_cache_entries()
        for entry in entries:
            entry_type = "🗂️  Complete" if entry['cache_type'] == 'complete' else "🔗 Individual"
            if entry['cache_type'] == 'complete':
                print(f"{entry_type}: {len(entry['urls'])} URLs, {entry['file_size_bytes']} bytes ({entry['age_hours']:.1f}h old)")
            else:
                print(f"{entry_type}: {entry['url']}, {entry['file_size_bytes']} bytes ({entry['age_hours']:.1f}h old)")

if __name__ == "__main__":
    test_cache_optimization() 