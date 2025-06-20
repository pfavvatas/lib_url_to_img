# Enhanced Caching System Guide

## Overview

The enhanced caching system provides intelligent, URL-aware caching for web scraping data to avoid expensive ChromeDriver operations and data collection processes.

## Features

### 🎯 URL-Aware Caching
- **Smart Cache Keys**: Uses SHA256 hash of URLs + levels combination
- **Content Validation**: Verifies cached data matches current request
- **Integrity Checks**: Validates file existence and metadata consistency

### ⏰ Flexible TTL (Time To Live)
- **API Calls**: Default 1 hour TTL for faster iteration
- **CLI Usage**: Default 24 hours TTL for development convenience
- **Custom TTL**: Override default values per request

### 📊 Advanced Cache Management
- **Statistics**: Track cache size, hit rates, processing times
- **Cleanup**: Remove expired entries automatically
- **Monitoring**: List all cache entries with metadata

## How It Works

### 1. Cache Key Generation
```python
# URLs: ["https://example.com", "https://test.com"]
# Levels: [1, 2, 3]
# Generated key: a1b2c3d4e5f6... (SHA256 hash)
```

### 2. Cache Structure
```
backend/api/cache/
├── cache_index.json           # Master index of all cache entries
├── data_a1b2c3d4.json        # Actual cached data
├── meta_a1b2c3d4.json        # Metadata (URLs, levels, timestamps)
├── data_f7e8d9c1.json        # Another cache entry
└── meta_f7e8d9c1.json        # Its metadata
```

### 3. Cache Validation Process
```
1. Generate cache key from URLs + levels
2. Check if entry exists in index
3. Verify files exist on disk
4. Check if cache hasn't expired
5. Validate URLs/levels match exactly
6. Return cached data or trigger fresh collection
```

## Usage Examples

### Programmatic Usage

```python
from utils.cache_manager import CacheManager

# Initialize cache manager
cache = CacheManager(cache_dir="cache", default_ttl_hours=24)

# Check for existing cache
urls = ["https://example.com", "https://test.com"]
levels = [1, 2, 3]
has_cache, cache_key = cache.has_valid_cache(urls, levels)

if has_cache:
    # Load cached data
    data = cache.get_cached_data(cache_key)
    print(f"✅ Using cached data: {len(data)} records")
else:
    # Process URLs and cache the result
    processed_data = your_processing_function(urls, levels)
    cache_key = cache.save_to_cache(urls, levels, processed_data, processing_time=120.5)
    print(f"💾 Data cached with key: {cache_key[:8]}...")
```

### API Endpoints

#### Get Cache Statistics
```bash
curl -X GET http://localhost:5000/cache/stats
```

Response:
```json
{
  "status": "success",
  "data": {
    "total_entries": 5,
    "total_size_mb": 45.2,
    "average_processing_time": 63.4,
    "oldest_entry": "2024-01-15T10:30:00",
    "newest_entry": "2024-01-15T14:20:00"
  }
}
```

#### List Cache Entries
```bash
curl -X GET http://localhost:5000/cache/entries
```

Response:
```json
{
  "status": "success",
  "data": [
    {
      "cache_key": "a1b2c3d4e5f6...",
      "urls": ["https://example.com"],
      "levels": [1, 2],
      "created_at": "2024-01-15T14:20:00",
      "age_hours": 2.5,
      "file_size_bytes": 1048576,
      "processing_time": 45.2,
      "num_records": 150
    }
  ]
}
```

#### Check Cache for Specific URLs
```bash
curl -X POST http://localhost:5000/cache/check \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "levels": [1, 2],
    "ttl_hours": 12
  }'
```

#### Clear All Cache
```bash
curl -X POST http://localhost:5000/cache/clear
```

#### Cleanup Expired Entries
```bash
curl -X POST http://localhost:5000/cache/cleanup \
  -H "Content-Type: application/json" \
  -d '{"ttl_hours": 6}'
```

## Configuration

### Cache Directory Structure
- **Default location**: `backend/api/cache/`
- **Customizable**: Pass `cache_dir` parameter to `CacheManager`
- **Auto-creation**: Directory created automatically if it doesn't exist

### TTL Configuration
```python
# Different TTL for different scenarios
cache_manager = CacheManager(
    cache_dir="cache",
    default_ttl_hours=24  # Default TTL
)

# Override TTL per request
has_cache, key = cache_manager.has_valid_cache(urls, levels, custom_ttl_hours=6)
```

### Environment Variables
You can set environment variables to configure caching:

```bash
export CACHE_TTL_HOURS=12        # Default TTL
export CACHE_DIR="/path/to/cache" # Custom cache directory
export ENABLE_CACHE_LOGGING=true  # Enable detailed logging
```

## Performance Benefits

### Before Enhanced Caching
```
🐌 Every request:
1. Start ChromeDriver (5-10 seconds)
2. Load each URL (10-30 seconds per URL)
3. Process DOM data (5-15 seconds per URL)
4. Generate computed styles (10-20 seconds)
Total: 30-75 seconds for a single URL
```

### After Enhanced Caching
```
⚡ With cache hit:
1. Check cache key (< 0.1 seconds)
2. Load cached data (0.5-2 seconds)
3. Skip to clustering/analysis
Total: < 3 seconds for cached data
```

**Performance Improvement**: 10-25x faster for cached requests!

## Monitoring and Maintenance

### Cache Statistics Monitoring
```python
stats = cache_manager.get_cache_stats()
print(f"Cache efficiency: {stats['total_entries']} entries")
print(f"Storage used: {stats['total_size_mb']:.1f} MB")
print(f"Average processing time: {stats['average_processing_time']:.1f}s")
```

### Automated Cleanup
```python
# Remove entries older than 7 days
removed = cache_manager.cleanup_expired(ttl_hours=168)
print(f"Cleaned up {removed} expired entries")
```

### Cache Health Check
```python
entries = cache_manager.list_cache_entries()
for entry in entries:
    if entry['age_hours'] > 24:
        print(f"Old entry: {entry['cache_key'][:8]}... (age: {entry['age_hours']:.1f}h)")
```

## Troubleshooting

### Cache Not Working
1. **Check permissions**: Ensure write access to cache directory
2. **Verify disk space**: Cache files can be large (10-100MB each)
3. **Check logs**: Enable logging to see cache operations

### Cache Corruption
```python
# Clear corrupted cache
cache_manager.clear_all_cache()
print("Cache cleared, fresh data will be collected")
```

### Performance Issues
1. **Large cache**: Use `cleanup_expired()` regularly
2. **Disk I/O**: Consider SSD storage for cache directory
3. **Memory usage**: Large datasets may require more RAM

## Best Practices

### 1. Regular Maintenance
```python
# Weekly cleanup script
def weekly_cache_maintenance():
    cache = CacheManager()
    
    # Remove entries older than 7 days
    removed = cache.cleanup_expired(ttl_hours=168)
    
    # Get statistics
    stats = cache.get_cache_stats()
    
    print(f"Maintenance complete: {removed} entries removed")
    print(f"Cache status: {stats['total_entries']} entries, {stats['total_size_mb']:.1f} MB")
```

### 2. Custom TTL Strategy
```python
# Different TTL based on data type
def get_cache_ttl(urls, levels):
    if len(urls) > 10:
        return 6  # Large datasets: shorter TTL
    elif any('news' in url for url in urls):
        return 2  # News sites: very short TTL
    else:
        return 24  # Standard TTL
```

### 3. Cache Warming
```python
# Pre-populate cache with common URL/level combinations
common_requests = [
    (["https://example.com"], [1, 2]),
    (["https://test.com"], [1]),
    # ... more combinations
]

for urls, levels in common_requests:
    if not cache_manager.has_valid_cache(urls, levels)[0]:
        # Process and cache this combination
        process_and_cache(urls, levels)
```

## Integration with Existing Code

The enhanced caching is automatically integrated into your existing workflow:

1. **CLI Usage**: Prompts user whether to use cached data
2. **API Usage**: Automatically uses cache if valid data exists
3. **Web Interface**: Cache statistics shown in UI (if implemented)

No changes needed to existing URL processing code!

## Security Considerations

### Cache Data Protection
- Cache files contain processed web data (not sensitive by default)
- Consider encryption for sensitive data scenarios
- Implement access controls on cache directory

### Cache Poisoning Prevention
- Cache keys include exact URL+level combinations
- Metadata validation prevents tampering
- File integrity checks detect corruption

## Future Enhancements

### Planned Features
- **Distributed caching**: Redis/Memcached support
- **Compression**: Reduce cache file sizes
- **Versioning**: Handle schema changes gracefully
- **Metrics export**: Prometheus/Grafana integration 