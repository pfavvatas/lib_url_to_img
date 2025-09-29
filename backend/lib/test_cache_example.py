#!/usr/bin/env python3
"""
Example script demonstrating the enhanced caching system.

This script shows how the caching system works in practice by:
1. Checking for existing cache
2. Processing URLs if no cache exists
3. Saving results to cache
4. Loading from cache on subsequent runs
"""

import os
import sys
import time
from datetime import datetime

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from cache_manager import CacheManager

def simulate_url_processing(urls, levels):
    """
    Simulate the expensive URL processing that we want to cache.
    In reality, this would involve ChromeDriver, DOM parsing, etc.
    """
    print(f"🔄 Simulating processing of {len(urls)} URLs, levels {levels}")
    
    # Simulate processing time
    processing_time = len(urls) * 2 + len(levels) * 0.5  # Simulate work
    for i in range(int(processing_time)):
        print(f"   Processing... {i+1}/{int(processing_time)}")
        time.sleep(0.2)  # Simulate work
    
    # Generate fake data that would normally come from web scraping
    fake_data = {}
    for i, url in enumerate(urls):
        for level in levels:
            guid = f"guid_{i}_{level}_{hash(url + str(level)) % 10000}"
            fake_data[guid] = {
                "url": url,
                "level": level,
                "html_data": {
                    "tag_name": "div",
                    "text": f"Sample content from {url} at level {level}",
                    "attributes": {
                        "class": f"sample-class-{level}",
                        "id": f"sample-id-{i}"
                    },
                    "children": []
                },
                "timestamp": datetime.now().isoformat(),
                "processed_at": f"level_{level}"
            }
    
    return fake_data, processing_time

def main():
    print("🚀 Enhanced Caching System Demo")
    print("=" * 50)
    
    # Example URLs and levels
    urls = [
        "https://example.com",
        "https://test.com",
        "https://demo.com"
    ]
    levels = [1, 2, 3]
    
    print(f"📋 Test Configuration:")
    print(f"   URLs: {urls}")
    print(f"   Levels: {levels}")
    print()
    
    # Initialize cache manager
    cache_dir = os.path.join(os.path.dirname(__file__), "demo_cache")
    cache_manager = CacheManager(cache_dir=cache_dir, default_ttl_hours=1)
    
    print(f"💾 Cache directory: {cache_dir}")
    
    # Show current cache stats
    stats = cache_manager.get_cache_stats()
    print(f"📊 Current cache: {stats['total_entries']} entries, {stats['total_size_mb']:.1f} MB")
    print()
    
    # Check for existing cache
    print("🔍 Checking for cached data...")
    start_time = time.time()
    
    has_cache, cache_key = cache_manager.has_valid_cache(urls, levels)
    cache_check_time = time.time() - start_time
    
    print(f"   Cache check took: {cache_check_time:.3f} seconds")
    print(f"   Cache key: {cache_key[:16]}...")
    
    if has_cache:
        print("✅ Found valid cached data!")
        
        # Load cached data
        load_start = time.time()
        cached_data = cache_manager.get_cached_data(cache_key)
        load_time = time.time() - load_start
        
        print(f"   Loading took: {load_time:.3f} seconds")
        print(f"   Records loaded: {len(cached_data)}")
        print("   🎉 ChromeDriver was NOT needed - huge time savings!")
        
        # Show sample data
        if cached_data:
            first_key = list(cached_data.keys())[0]
            sample = cached_data[first_key]
            print(f"\n📄 Sample cached record:")
            print(f"   GUID: {first_key}")
            print(f"   URL: {sample['url']}")
            print(f"   Level: {sample['level']}")
            print(f"   Cached at: {sample['timestamp']}")
        
    else:
        print("❌ No valid cache found - will process URLs")
        print("   ⚠️  This will take longer as ChromeDriver would be used")
        
        # Simulate the expensive processing
        process_start = time.time()
        processed_data, processing_time = simulate_url_processing(urls, levels)
        actual_process_time = time.time() - process_start
        
        print(f"   Processing took: {actual_process_time:.1f} seconds")
        print(f"   Generated {len(processed_data)} records")
        
        # Save to cache
        save_start = time.time()
        cache_key = cache_manager.save_to_cache(urls, levels, processed_data, processing_time)
        save_time = time.time() - save_start
        
        print(f"   Caching took: {save_time:.3f} seconds")
        print(f"   Saved with key: {cache_key[:16]}...")
    
    print()
    
    # Show updated cache stats
    print("📊 Final cache statistics:")
    final_stats = cache_manager.get_cache_stats()
    print(f"   Total entries: {final_stats['total_entries']}")
    print(f"   Total size: {final_stats['total_size_mb']:.1f} MB")
    print(f"   Average processing time: {final_stats['average_processing_time']:.1f} seconds")
    
    # List all cache entries
    print("\n📋 All cache entries:")
    entries = cache_manager.list_cache_entries()
    for i, entry in enumerate(entries, 1):
        age_hours = entry['age_hours']
        age_str = f"{age_hours*60:.0f}m" if age_hours < 1 else f"{age_hours:.1f}h"
        size_mb = entry['file_size_bytes'] / (1024 * 1024)
        
        print(f"   #{i} Key: {entry['cache_key'][:12]}... "
              f"Age: {age_str}, Size: {size_mb:.1f}MB, "
              f"URLs: {len(entry['urls'])}, Records: {entry['num_records']}")
    
    print("\n🎯 Demo complete!")
    print("\n💡 Next steps:")
    print("   1. Run this script again to see cache hit in action")
    print("   2. Try: python cache_cli.py stats")
    print("   3. Try: python cache_cli.py list --detailed")
    print("   4. Try: python cache_cli.py cleanup --hours 0.5")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc() 