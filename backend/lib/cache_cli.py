#!/usr/bin/env python3
"""
Cache Management CLI Tool

This tool provides command-line access to cache management functions.
Usage examples:
    python cache_cli.py stats
    python cache_cli.py list
    python cache_cli.py cleanup --hours 48
    python cache_cli.py clear --confirm
    python cache_cli.py check --urls "https://example.com,https://test.com" --levels "1,2,3"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from cache_manager import CacheManager

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def format_size(bytes_size: int) -> str:
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def format_duration(seconds: float) -> str:
    """Format seconds to human readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def format_age(hours: float) -> str:
    """Format age in hours to human readable format."""
    if hours < 1:
        return f"{hours*60:.0f}m"
    elif hours < 24:
        return f"{hours:.1f}h"
    else:
        return f"{hours/24:.1f}d"

def print_stats(cache_manager: CacheManager):
    """Print cache statistics."""
    stats = cache_manager.get_cache_stats()
    
    print("📊 Cache Statistics")
    print("=" * 50)
    print(f"Total entries:        {stats['total_entries']}")
    print(f"Total size:           {format_size(stats['total_size_mb'] * 1024 * 1024)}")
    print(f"Average proc. time:   {format_duration(stats['average_processing_time'])}")
    
    if stats['oldest_entry']:
        oldest = datetime.fromisoformat(stats['oldest_entry'])
        newest = datetime.fromisoformat(stats['newest_entry'])
        oldest_age = (datetime.now() - oldest).total_seconds() / 3600
        newest_age = (datetime.now() - newest).total_seconds() / 3600
        
        print(f"Oldest entry:         {format_age(oldest_age)} ago ({oldest.strftime('%Y-%m-%d %H:%M')})")
        print(f"Newest entry:         {format_age(newest_age)} ago ({newest.strftime('%Y-%m-%d %H:%M')})")
    else:
        print("Oldest entry:         None")
        print("Newest entry:         None")

def print_entries(cache_manager: CacheManager, detailed: bool = False):
    """Print list of cache entries."""
    entries = cache_manager.list_cache_entries()
    
    if not entries:
        print("📭 No cache entries found")
        return
    
    print(f"📋 Cache Entries ({len(entries)} total)")
    print("=" * 80)
    
    if detailed:
        for i, entry in enumerate(entries, 1):
            print(f"\n#{i} Cache Key: {entry['cache_key'][:16]}...")
            print(f"   URLs ({len(entry['urls'])}): {', '.join(entry['urls'][:2])}" + 
                  (f" + {len(entry['urls'])-2} more" if len(entry['urls']) > 2 else ""))
            print(f"   Levels: {entry['levels']}")
            print(f"   Age: {format_age(entry['age_hours'])}")
            print(f"   Size: {format_size(entry['file_size_bytes'])}")
            print(f"   Records: {entry['num_records']}")
            print(f"   Proc. time: {format_duration(entry['processing_time'])}")
            print(f"   Created: {datetime.fromisoformat(entry['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        # Compact table format
        print(f"{'Key':<12} {'Age':<8} {'Size':<10} {'Records':<8} {'URLs':<6} {'Levels'}")
        print("-" * 80)
        for entry in entries:
            key_short = entry['cache_key'][:10] + ".."
            age = format_age(entry['age_hours'])
            size = format_size(entry['file_size_bytes'])
            records = str(entry['num_records'])
            url_count = str(len(entry['urls']))
            levels = str(entry['levels'])[:20] + ("..." if len(str(entry['levels'])) > 20 else "")
            
            print(f"{key_short:<12} {age:<8} {size:<10} {records:<8} {url_count:<6} {levels}")

def check_cache(cache_manager: CacheManager, urls: List[str], levels: List[int], ttl_hours: int = None):
    """Check if cache exists for specific URLs and levels."""
    print(f"🔍 Checking cache for:")
    print(f"   URLs: {urls}")
    print(f"   Levels: {levels}")
    if ttl_hours:
        print(f"   Custom TTL: {ttl_hours} hours")
    
    has_cache, cache_key = cache_manager.has_valid_cache(urls, levels, ttl_hours)
    
    if has_cache:
        print(f"✅ Valid cache found!")
        print(f"   Cache key: {cache_key}")
        
        # Get cache entry details
        entries = cache_manager.list_cache_entries()
        entry = next((e for e in entries if e['cache_key'] == cache_key), None)
        if entry:
            print(f"   Age: {format_age(entry['age_hours'])}")
            print(f"   Size: {format_size(entry['file_size_bytes'])}")
            print(f"   Records: {entry['num_records']}")
    else:
        print(f"❌ No valid cache found")
        print(f"   Generated key would be: {cache_key[:16]}...")

def cleanup_cache(cache_manager: CacheManager, ttl_hours: int):
    """Clean up expired cache entries."""
    print(f"🧹 Cleaning up entries older than {ttl_hours} hours...")
    
    removed_count = cache_manager.cleanup_expired(ttl_hours)
    
    if removed_count > 0:
        print(f"✅ Removed {removed_count} expired entries")
    else:
        print("✨ No expired entries found")

def clear_cache(cache_manager: CacheManager, confirm: bool = False):
    """Clear all cache entries."""
    if not confirm:
        print("⚠️  This will delete ALL cached data!")
        response = input("Are you sure? Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return
    
    print("🗑️  Clearing all cache...")
    removed_count = cache_manager.clear_all_cache()
    print(f"✅ Cleared {removed_count} cache entries")

def main():
    parser = argparse.ArgumentParser(
        description="Cache Management CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s stats                                    # Show cache statistics
  %(prog)s list                                     # List cache entries (compact)
  %(prog)s list --detailed                          # List cache entries (detailed)
  %(prog)s cleanup --hours 24                      # Remove entries older than 24h
  %(prog)s clear --confirm                          # Clear all cache (skip confirmation)
  %(prog)s check --urls "site1.com,site2.com" --levels "1,2,3"  # Check specific cache
        """
    )
    
    parser.add_argument(
        '--cache-dir', 
        default=os.path.join(PROJECT_ROOT, "backend", "api", "cache"),
        help='Cache directory path (default: backend/api/cache)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List cache entries')
    list_parser.add_argument('--detailed', action='store_true', 
                            help='Show detailed information for each entry')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check if cache exists for specific URLs/levels')
    check_parser.add_argument('--urls', required=True, 
                             help='Comma-separated list of URLs')
    check_parser.add_argument('--levels', required=True, 
                             help='Comma-separated list of levels (integers)')
    check_parser.add_argument('--ttl', type=int, 
                             help='Custom TTL in hours')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove expired cache entries')
    cleanup_parser.add_argument('--hours', type=int, default=24,
                               help='Remove entries older than this many hours (default: 24)')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all cache entries')
    clear_parser.add_argument('--confirm', action='store_true',
                             help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize cache manager
    try:
        cache_manager = CacheManager(cache_dir=args.cache_dir)
    except Exception as e:
        print(f"❌ Error initializing cache manager: {e}")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == 'stats':
            print_stats(cache_manager)
            
        elif args.command == 'list':
            print_entries(cache_manager, detailed=args.detailed)
            
        elif args.command == 'check':
            urls = [url.strip() for url in args.urls.split(',')]
            levels = [int(level.strip()) for level in args.levels.split(',')]
            check_cache(cache_manager, urls, levels, args.ttl)
            
        elif args.command == 'cleanup':
            cleanup_cache(cache_manager, args.hours)
            
        elif args.command == 'clear':
            clear_cache(cache_manager, args.confirm)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 