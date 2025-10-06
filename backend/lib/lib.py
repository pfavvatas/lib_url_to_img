# FILE: ./lib/main.py

import argparse
from utils import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os
import json
import time
from urllib.parse import urlparse
import stat
import subprocess
import platform
import traceback
import zipfile
import random
import glob
import numpy as np
from utils.clustering import perform_clustering_analysis
from utils.site_similarity import compute_site_cosine_similarity
from utils.cache_manager import CacheManager

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ======================================
# GLOBAL CACHE CONFIGURATION
# ======================================
# TO ENABLE CACHING: Change False to True below
# TO DISABLE CACHING: Change True to False below
ENABLE_CACHING = True  # 🔧 MAIN CACHE SWITCH: Set to True to enable caching, False to disable

# When ENABLE_CACHING = True:
#   - URLs and processing results are cached for faster subsequent runs
#   - Cache TTL: 24 hours for CLI, 1 hour for API calls
#   - Both complete and partial cache hits are supported
#   - User prompts for cache usage in CLI mode
# When ENABLE_CACHING = False:
#   - All URLs are processed fresh every time
#   - No cache checking or saving occurs
#   - Faster startup, but slower processing for repeated URL sets

def find_chromedriver(port=9515):
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['where', 'chromedriver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(['which', 'chromedriver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0 and result.stdout:
            chromedriver_path = result.stdout.strip()
            print(f"ChromeDriver found at: {chromedriver_path}")
            
            # Create and start the Service
            service = Service(chromedriver_path, port=port)
            service.start()
            return service
        else:
            print("ChromeDriver not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        

def process_urls_from_cli(urls, levels, from_api=False):
    """
    Process URLs from CLI or API with clustering analysis.
    
    CACHE CONFIGURATION:
    Cache status is controlled by the global ENABLE_CACHING variable at the top of this file.
    Set ENABLE_CACHING = True to enable caching system
    Set ENABLE_CACHING = False to disable caching (current setting)
    """
    
    print(f"DEBUG: process_urls_from_cli called with urls={urls}, levels={levels}, from_api={from_api}")
    print(f"🔧 CACHE STATUS: {'ENABLED' if ENABLE_CACHING else 'DISABLED'}")
    
    # Initialize timing logs
    timing_logs = {
        "total_start_time": time.time(),
        "steps": {},
        "cluster_info": {},
        "performance_metrics": {}
    }
    
    print(f"DEBUG: Timing logs initialized: {list(timing_logs.keys())}")
    
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = Config(config_path)

    debug_mode = getattr(config, 'debug', False)
    if debug_mode: print(config)
    
    # ======================================
    # CACHING SYSTEM - CONFIGURABLE
    # ======================================
    # Initialize cache manager (always needed for compatibility)
    cache_dir = os.path.join(PROJECT_ROOT, "backend", "api", "cache")
    cache_ttl_hours = 2160 #24 if not from_api else 1  # 24 hours for CLI, 1 hour for API
    cache_manager = CacheManager(cache_dir=cache_dir, default_ttl_hours=cache_ttl_hours)
    
    # Step 1: Check for cached data (conditional on ENABLE_CACHING)
    step_start = time.time()
    
    if ENABLE_CACHING:
        # CACHING ENABLED - Full cache checking logic
        has_complete_cache, cache_key = cache_manager.has_valid_cache(urls, levels, cache_ttl_hours)
        cached_url_data, urls_to_process = cache_manager.get_partial_cached_data(urls, levels, cache_ttl_hours)
        
        will_skip_data_collection = False
        complete_cached_data = None
        
        # Check for complete cache first
        if has_complete_cache:
            complete_cached_data = cache_manager.get_cached_data(cache_key)
            if complete_cached_data:
                will_skip_data_collection = True
                cache_stats = cache_manager.get_cache_stats()
                print(f"\033[92m✅ Found COMPLETE cached data (key: {cache_key[:8]}...)\033[0m")
                print(f"\033[94m📊 Cache stats: {cache_stats['total_entries']} entries, {cache_stats['total_size_mb']:.1f} MB total\033[0m")
            else:
                print(f"\033[93m⚠️  Complete cache key found but data corrupted, checking partial cache\033[0m")
        
        # Check partial cache if no complete cache
        if not will_skip_data_collection and cached_url_data:
            print(f"\033[96m🔍 Found PARTIAL cached data for {len(urls) - len(urls_to_process)}/{len(urls)} URLs\033[0m")
            print(f"\033[96m📋 URLs from cache: {[url for url in urls if url not in urls_to_process]}\033[0m")
            print(f"\033[96m🔄 URLs to process: {urls_to_process}\033[0m")
            
            cache_stats = cache_manager.get_cache_stats()
            print(f"\033[94m📊 Cache stats: {cache_stats['complete_cache_entries']} complete + {cache_stats['individual_url_entries']} individual entries\033[0m")
        elif not will_skip_data_collection and not cached_url_data:
            print(f"\033[93m❌ No cached data found - will process all {len(urls)} URLs\033[0m")
        
        if not from_api and (has_complete_cache or cached_url_data):
            # For CLI usage, still prompt user about cached data
            cache_type = "complete" if has_complete_cache else "partial"
            cache_detail = f"all {len(urls)} URLs" if has_complete_cache else f"{len(urls) - len(urls_to_process)}/{len(urls)} URLs"
            print(f"\033[93mFound {cache_type} cached data for {cache_detail}. Use cached data? (y/n)\033[0m")
            user_input = input().lower().strip()
            
            if user_input in ['y', 'yes']:
                if has_complete_cache and complete_cached_data:
                    will_skip_data_collection = True
                elif cached_url_data:
                    # Use partial cache - will only process missing URLs
                    pass
            else:
                # User chose not to use cache
                will_skip_data_collection = False
                cached_url_data = {}
                urls_to_process = urls.copy()
    else:
        # CACHING DISABLED - Process all URLs fresh
        has_complete_cache = False
        cache_key = None
        cached_url_data = {}
        urls_to_process = urls.copy()  # Process all URLs
        will_skip_data_collection = False
        complete_cached_data = None
        
        print(f"\033[93m🚫 Caching DISABLED - will process all {len(urls)} URLs fresh\033[0m")
    
    cache_check_time = time.time() - step_start

    # Step 2: ChromeDriver setup timing (conditional)
    driver = None
    if will_skip_data_collection:
        print(f"\033[93mSkipping ChromeDriver setup - using complete cached data\033[0m")
    elif not urls_to_process:
        print(f"\033[93mSkipping ChromeDriver setup - all URLs cached individually\033[0m")
    else:
        print(f"\033[94mSetting up ChromeDriver for {len(urls_to_process)} URLs\033[0m")
        service = find_chromedriver()
        if service:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.binary_location = "/opt/google/chrome/chrome"  # Specify the correct path to your Chrome binary
            driver = webdriver.Chrome(service=service, options=chrome_options)
    
    timing_logs["steps"]["cache_check"] = {
        "start_time": step_start,
        "end_time": step_start + cache_check_time,
        "duration": cache_check_time,
        "description": f"Cache checking ({'ENABLED' if ENABLE_CACHING else 'DISABLED - processing all URLs fresh'})",
        "complete_cache_hit": has_complete_cache and will_skip_data_collection if ENABLE_CACHING else False,
        "partial_cache_hit": bool(cached_url_data) if ENABLE_CACHING else False,
        "cached_urls_count": len(urls) - len(urls_to_process) if ENABLE_CACHING else 0,
        "urls_to_process_count": len(urls_to_process),
        "cache_key": cache_key if ENABLE_CACHING else None,
        "will_use_complete_cache": will_skip_data_collection if ENABLE_CACHING else False,
        "will_use_partial_cache": bool(cached_url_data) and not will_skip_data_collection if ENABLE_CACHING else False,
        "cache_disabled": not ENABLE_CACHING
    }
    
    timing_logs["steps"]["chromedriver_setup"] = {
        "start_time": step_start + cache_check_time,
        "end_time": time.time(),
        "duration": time.time() - (step_start + cache_check_time),
        "description": f"ChromeDriver initialization and configuration for {len(urls_to_process)} URLs" + 
                      (" (skipped - complete cache)" if will_skip_data_collection else 
                       " (skipped - all cached)" if not urls_to_process else ""),
        "skipped": will_skip_data_collection or not urls_to_process
    }

    # Step 3: Data collection timing (with enhanced caching)
    step_start = time.time()
    dataCollector = DataCollector()
    
    if will_skip_data_collection and complete_cached_data:
        # Load complete cached data
        dataCollector.url_data = complete_cached_data
        dataCollector.timing_logs = {"data_collection": {"description": "Skipped - using complete cached data", "duration": 0}}
        dataCollector.url_timing_logs = {}
        print(f"\033[92m✅ Loaded {len(complete_cached_data)} cached records for {len(urls)} URLs (COMPLETE CACHE)\033[0m")
    
    elif urls_to_process:
        # Collect new data for non-cached URLs
        print(f"\033[94m🔄 Starting data collection for {len(urls_to_process)} non-cached URLs\033[0m")
        if cached_url_data:
            print(f"\033[96m📦 Using cached data for {len(urls) - len(urls_to_process)} URLs\033[0m")
        
        data_collection_start = time.time()
        
        if driver is None:
            # If driver setup was skipped, we need to set it up now
            service = find_chromedriver()
            if service:
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.binary_location = "/opt/google/chrome/chrome"
                driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Collect data for new URLs only
        dataCollector.collect_data(urls_to_process, levels, driver, config)
        
        # Merge with cached data if available
        if cached_url_data and ENABLE_CACHING:
            merged_data = {**cached_url_data, **dataCollector.url_data}
            dataCollector.url_data = merged_data
            print(f"\033[96m🔗 Merged {len(cached_url_data)} cached + {len(dataCollector.url_data) - len(cached_url_data)} new records\033[0m")
        
        # Cache saving logic - conditional on ENABLE_CACHING
        data_collection_time = time.time() - data_collection_start
        if ENABLE_CACHING:
            # Save ALL data to cache (complete set)
            cache_key = cache_manager.save_to_cache(urls, levels, dataCollector.url_data, data_collection_time)
            print(f"\033[92m💾 Data saved to cache (key: {cache_key[:8]}..., processing time: {data_collection_time:.2f}s)\033[0m")
        else:
            cache_key = None
            print(f"\033[93m🚫 Cache saving DISABLED - data not saved to cache (processing time: {data_collection_time:.2f}s)\033[0m")
    
    else:
        # All URLs are cached individually (only happens when caching is enabled)
        if ENABLE_CACHING and cached_url_data:
            dataCollector.url_data = cached_url_data
            dataCollector.timing_logs = {"data_collection": {"description": "Skipped - all URLs cached individually", "duration": 0}}
            dataCollector.url_timing_logs = {}
            print(f"\033[92m✅ All {len(urls)} URLs found in cache - no processing needed!\033[0m")
            
            # Save complete cache entry for this combination for future use
            cache_key = cache_manager.save_to_cache(urls, levels, dataCollector.url_data, 0)
            print(f"\033[96m📦 Created complete cache entry for this URL combination (key: {cache_key[:8]}...)\033[0m")
        else:
            # This shouldn't happen when caching is disabled, but handle it gracefully
            dataCollector.url_data = {}
            dataCollector.timing_logs = {"data_collection": {"description": "No data to process", "duration": 0}}
            dataCollector.url_timing_logs = {}
            cache_key = None
            print(f"\033[93m🚫 No data to process (caching disabled)\033[0m")
    
    timing_logs["steps"]["data_collection"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": f"URL data collection and processing ({'CACHE ENABLED' if ENABLE_CACHING else 'CACHE DISABLED - all URLs processed fresh'})",
        "urls_processed": len(urls_to_process),
        "urls_from_cache": len(urls) - len(urls_to_process) if ENABLE_CACHING else 0,
        "total_urls": len(urls),
        "levels_processed": levels,
        "cache_efficiency": f"{((len(urls) - len(urls_to_process)) / len(urls) * 100):.1f}%" if ENABLE_CACHING and len(urls) > 0 else "0.0%",
        "data_reused": bool(cached_url_data) if ENABLE_CACHING else False,
        "cache_type": ("complete" if will_skip_data_collection else "partial" if cached_url_data else "none") if ENABLE_CACHING else "disabled",
        "cache_key": cache_key,
        "cache_disabled": not ENABLE_CACHING,
        "detailed_timing": dataCollector.timing_logs,  # Include detailed timing from DataCollector
        "url_timing_logs": dataCollector.url_timing_logs  # Include per-URL detailed timing
    }

    # Step 3: Data saving timing
    step_start = time.time()
    dataCollector.save_data()
    timing_logs["steps"]["data_saving"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Saving collected data to JSON files",
        "detailed_timing": dataCollector.timing_logs.get("data_saving", {})
    }

    # Step 4: Computed styles generation timing
    step_start = time.time()
    print(f"\033[94m=== Starting computed styles generation for all levels ===\033[0m")
    computed_styles_paths = {}
    total_unique_attributes = None
    for level in levels:
        print(f"\033[94m=== Starting computed styles generation for level {level} ===\033[0m")
        tua, attribute_values, cs_file = dataCollector.computed_styles(level=level)
        if total_unique_attributes is None:
            total_unique_attributes = tua
        computed_styles_paths[level] = cs_file
        print(f"\033[94m=== Finished computed styles generation for level {level} in {time.time() - step_start:.4f}s ===\033[0m")
    print(f"\033[94m=== Finished computed styles generation for all levels in {time.time() - step_start:.4f}s ===\033[0m")
    timing_logs["steps"]["computed_styles_generation"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Generating computed styles for all levels",
        "levels_processed": levels,
        "total_unique_attributes": total_unique_attributes,
        "detailed_timing": {f"level_{level}": dataCollector.timing_logs.get(f"computed_styles_level_{level}", {}) for level in levels}
    }

    # Step 5: Image data collection timing
    step_start = time.time()
    image_data_collector = ImageDataCollector(dataCollector.url_data)
    image_data_collector.save_to_json()
    timing_logs["steps"]["image_data_collection"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Image data collection and processing"
    }
    
    if driver:
        driver.close()    
    
    # Step 6: Clustering processing timing
    clustering_results = []
    processed_clusters_data = []
    created_html_files = []  # Track created HTML files
    
    for level in levels:
        level_start_time = time.time()
        
        # Get the computed styles file path for this level (re-use from earlier generation)
        computed_styles_file = computed_styles_paths.get(level)
        # print(f"\033[92m computed_styles_file: {computed_styles_file}\033[0m")

        # Process the computed styles file and call clustering function directly
        try:
            # Read the computed styles data
            clustering_read_start = time.time()
            with open(computed_styles_file, 'r') as file:
                data = json.load(file)
            clustering_read_time = time.time() - clustering_read_start
            
            # Get file size information
            file_size = os.path.getsize(computed_styles_file) if os.path.exists(computed_styles_file) else 0
            
            print(f"\033[94m=== CLUSTERING RESULTS FOR LEVEL {level} ===\033[0m")
            print(f"\033[92mComputed styles file: {computed_styles_file}\033[0m")
            
            # Call the clustering function with the data directly
            clustering_analysis_start = time.time()
            print(f"\033[94m=== Starting clustering analysis for level {level} ===\033[0m")
            clustering_result = perform_clustering_analysis(data)
            clustering_analysis_time = time.time() - clustering_analysis_start
            print(f"\033[94m=== Finished clustering analysis for level {level} in {clustering_analysis_time:.4f}s ===\033[0m")
            
            if clustering_result['success']:
                print(f"\033[92mStatus: success\033[0m")
                print(f"\033[92mMessage: {clustering_result['message']}\033[0m")
                
                print(f"\033[93mNumber of clusters: {clustering_result['cluster_info']['num_clusters']}\033[0m")
                print(f"\033[93mDBCV Score: {clustering_result['cluster_info']['dbcv_score']:.3f}\033[0m")
                print(f"\033[93mClusters: {clustering_result['clusters']}\033[0m")
                
                # Store cluster info in timing logs
                timing_logs["cluster_info"][f"level_{level}"] = clustering_result['cluster_info']
                
                # Add level information to the result
                clustering_result['level'] = level
                clustering_results.append(clustering_result)

                # Process clusters for this level
                if 'clusters' in clustering_result:
                    cluster_processing_start = time.time()
                    cluster_data = json.dumps(clustering_result['clusters'])
                    processed_cluster = process_clusters_from_cli(cluster_data, from_api=True, level_info=level)
                    cluster_processing_time = time.time() - cluster_processing_start
                    
                    processed_clusters_data.append({
                        'level': level,
                        'processed_data': processed_cluster,
                        'timing_logs': processed_cluster.get('timing_logs', {})  # Include timing logs from cluster processing
                    })
                    
                    # Track HTML files from processed_cluster
                    if isinstance(processed_cluster, dict):
                        if 'html_files' in processed_cluster:
                            created_html_files.extend(processed_cluster['html_files'])
                        elif 'data' in processed_cluster:
                            try:
                                data_lines = processed_cluster['data'].split('\n')
                                for line in data_lines:
                                    if line.startswith('File created:'):
                                        file_path = line.replace('File created: ', '').strip()
                                        if file_path.endswith('.html'):
                                            created_html_files.append({
                                                'filename': os.path.basename(file_path),
                                                'path': os.path.basename(file_path)  # Remove the "output_html_files/" prefix
                                            })
                            except Exception as e:
                                print(f"Error processing HTML files: {e}")
                
                # Store level-specific timing with detailed information
                timing_logs["steps"][f"clustering_level_{level}"] = {
                    "start_time": level_start_time,
                    "end_time": time.time(),
                    "duration": time.time() - level_start_time,
                    "description": f"Complete clustering processing for level {level}",
                    "level": level,
                    "computed_styles_file": computed_styles_file,
                    "file_size_bytes": file_size,
                    "file_size_mb": file_size / (1024 * 1024),
                    "clusters_generated": clustering_result['cluster_info']['num_clusters'] if clustering_result['success'] else 0,
                    "dbcv_score": clustering_result['cluster_info']['dbcv_score'] if clustering_result['success'] else 0,
                    "useful_attributes_count": len(clustering_result['cluster_info']['useful_attributes']) if clustering_result['success'] else 0,
                    "sub_steps": {
                        "file_reading": {
                            "duration": clustering_read_time,
                            "description": "Reading computed styles file",
                            "file_size_bytes": file_size,
                            "file_size_mb": file_size / (1024 * 1024)
                        },
                        "clustering_analysis": {
                            "duration": clustering_analysis_time,
                            "description": "Performing clustering analysis",
                            "algorithm": "HDBSCAN",
                            "success": clustering_result['success'],
                            "message": clustering_result['message']
                        },
                        "cluster_processing": {
                            "duration": cluster_processing_time,
                            "description": "Processing cluster results and generating HTML",
                            "html_files_created": len(created_html_files) if isinstance(processed_cluster, dict) and 'html_files' in processed_cluster else 0
                        }
                    }
                }
            else:
                clustering_results.append({
                    "level": level,
                    "status": "error",
                    "message": f"Level {level}: {clustering_result['message']}"
                })
                
                timing_logs["steps"][f"clustering_level_{level}"] = {
                    "start_time": level_start_time,
                    "end_time": time.time(),
                    "duration": time.time() - level_start_time,
                    "description": f"Clustering processing for level {level} (ERROR)",
                    "level": level,
                    "computed_styles_file": computed_styles_file,
                    "file_size_bytes": file_size,
                    "file_size_mb": file_size / (1024 * 1024),
                    "error": clustering_result['message'],
                    "sub_steps": {
                        "file_reading": {
                            "duration": clustering_read_time,
                            "description": "Reading computed styles file",
                            "file_size_bytes": file_size,
                            "file_size_mb": file_size / (1024 * 1024)
                        },
                        "clustering_analysis": {
                            "duration": clustering_analysis_time,
                            "description": "Performing clustering analysis",
                            "algorithm": "HDBSCAN",
                            "success": False,
                            "error": clustering_result['message']
                        }
                    }
                }
            
            print(f"\033[94m=== END CLUSTERING RESULTS ===\033[0m\n")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"\033[91mError during clustering: {str(e)}\033[0m")
            print(f"\033[91mStack trace: {error_details}\033[0m")
            clustering_results.append({
                "level": level,
                "status": "error",
                "message": f"Level {level}: Error during clustering: {str(e)}",
                "stack_trace": error_details
            })
            
            timing_logs["steps"][f"clustering_level_{level}"] = {
                "start_time": level_start_time,
                "end_time": time.time(),
                "duration": time.time() - level_start_time,
                "description": f"Clustering processing for level {level} (EXCEPTION)",
                "level": level,
                "computed_styles_file": computed_styles_file,
                "error": str(e),
                "stack_trace": error_details
            }
    
    # Calculate total processing time
    timing_logs["total_end_time"] = time.time()
    timing_logs["total_duration"] = timing_logs["total_end_time"] - timing_logs["total_start_time"]
    
    # Find best clustering level using median-based algorithm
    best_level_info = find_best_clustering_level(clustering_results)
    if best_level_info:
        print(f"\033[93m🏆 BEST CLUSTERING LEVEL DETECTED: Level {best_level_info['best_level']}\033[0m")
        print(f"\033[93m   📊 {best_level_info['algorithm_details']['selection_reason']}\033[0m")
        print(f"\033[93m   🔍 Algorithm: Median of {best_level_info['algorithm_details']['total_valid_levels']} levels, W={best_level_info['algorithm_details']['w_cluster_count']}, filtered {best_level_info['algorithm_details']['filtered_candidates']} candidates\033[0m")
        
        # Mark the best level in clustering results
        for result in clustering_results:
            if result.get('level') == best_level_info['best_level']:
                result['is_best_level'] = True
                result['best_level_details'] = best_level_info['algorithm_details']
        
        # Mark the best level in processed clusters
        for processed_cluster in processed_clusters_data:
            if processed_cluster.get('level') == best_level_info['best_level']:
                processed_cluster['is_best_level'] = True
                processed_cluster['best_level_details'] = best_level_info['algorithm_details']
    else:
        print(f"\033[94m📊 No best clustering level detected (insufficient valid results for comparison)\033[0m")
    
    # Calculate performance metrics (conditional on caching)
    urls_from_cache = len(urls) - len(urls_to_process) if ENABLE_CACHING else 0
    cache_efficiency = (urls_from_cache / len(urls) * 100) if ENABLE_CACHING and len(urls) > 0 else 0.0
    
    timing_logs["performance_metrics"] = {
        "total_processing_time": timing_logs["total_duration"],
        "average_time_per_url": timing_logs["total_duration"] / len(urls) if urls else 0,
        "average_time_per_level": timing_logs["total_duration"] / len(levels) if levels else 0,
        "urls_processed": len(urls),
        "urls_from_cache": urls_from_cache,
        "urls_newly_processed": len(urls_to_process),
        "cache_efficiency_percent": cache_efficiency,
        "levels_processed": len(levels),
        "html_files_generated": len(created_html_files),
        "clusters_generated": sum(len(result.get('clusters', [])) for result in clustering_results if result.get('status') != 'error'),
        "cache_savings": f"Saved processing {urls_from_cache}/{len(urls)} URLs ({cache_efficiency:.1f}%)" if ENABLE_CACHING and urls_from_cache > 0 else ("Cache disabled - no savings" if not ENABLE_CACHING else "No cache savings this run"),
        "cache_disabled": not ENABLE_CACHING
    }
    
    print(f"DEBUG: About to return timing logs. Keys: {list(timing_logs.keys())}")
    print(f"DEBUG: Performance metrics: {timing_logs.get('performance_metrics', {})}")
    
    if ENABLE_CACHING:
        if urls_from_cache > 0:
            print(f"\033[92m💾 CACHING ENABLED: Saved processing {urls_from_cache}/{len(urls)} URLs ({cache_efficiency:.1f}% cache efficiency)\033[0m")
        else:
            print(f"\033[94m💾 CACHING ENABLED: No cache hits this run - processed all {len(urls)} URLs fresh\033[0m")
    else:
        print(f"\033[93m🚫 CACHING DISABLED: Processed all {len(urls)} URLs fresh - no cache savings\033[0m")
    
    if from_api:
        print(f"DEBUG: Timing logs keys: {list(timing_logs.keys())}")
        print(f"DEBUG: Performance metrics: {timing_logs.get('performance_metrics', {})}")
        return {
            "status": "success", 
            "message": "URLs processed successfully", 
            "file": computed_styles_file, 
            "clustering_results": clustering_results,
            "processed_clusters": processed_clusters_data,
            "html_files": created_html_files,  # Include only the created HTML files
            "timing_logs": timing_logs,  # Add timing logs to the response
            "best_level_info": best_level_info  # Add best level information
        }
    else:
        return {
            "status": "success", 
            "message": "URLs processed successfully", 
            "clustering_results": clustering_results,
            "processed_clusters": processed_clusters_data,
            "html_files": created_html_files,  # Include only the created HTML files
            "timing_logs": timing_logs,  # Add timing logs to the response
            "best_level_info": best_level_info  # Add best level information
        }


def process_clusters_from_cli(clusters_data, from_api=False, level_info=None):
    # Initialize timing logs for cluster processing
    cluster_timing_logs = {
        "start_time": time.time(),
        "steps": {},
        "file_operations": {}
    }
    
    class Cluster:
        def __init__(self, id, color, guids):
            self.id = id
            self.color = color
            self.guids = guids
            self.additional_info = None  # Placeholder for additional information

        def set_additional_info(self, info):
            self.additional_info = info

        def __repr__(self):
            return f"Cluster(id={self.id}, color={self.color}, guids={len(self.guids)}, additional_info={self.additional_info})"
        
        def print_results_one_line(self):
            return f"Cluster(id={self.id}, color={self.color}, guids={len(self.guids)}, additional_info={self.additional_info})"
        
    # Custom JSON encoder for Cluster objects
    class ClusterEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Cluster):
                return obj.__dict__
            return super().default(obj)
    
    # Step 1: Data parsing and cluster creation
    step_start = time.time()
    data = clusters_data
    data = json.loads(data)
        
    # List of 30 different colors
    colors = [
        "red", "blue", "green", "yellow", "purple", "orange", "pink", "brown", #"black", "white",
        "gray", "cyan", "magenta", "lime", "maroon", "navy", "olive", "teal", "aqua", "fuchsia",
        "silver", "gold", "beige", "coral", "indigo", "ivory", "khaki", "lavender", "plum", "salmon"
    ]
    
    # Function to generate a random color
    def generate_random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    # Create Cluster objects from data
    clusters = []
    for i, guids in enumerate(data):
        if i < len(colors):
            color = colors[i]
        else:
            color = generate_random_color()
        cluster = Cluster(id=f"cluster_{i}", color=color, guids=guids)
        clusters.append(cluster)
    
    cluster_timing_logs["steps"]["data_parsing"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Parsing cluster data and creating cluster objects",
        "clusters_created": len(clusters)
    }
        
    data_to_return = []
    # Print clusters to verify
    for cluster in clusters:
        print(cluster)
        data_to_return.append(cluster.print_results_one_line())
        
    # Step 2: GUID collection and site mapping
    step_start = time.time()
    # Collect all GUIDs from clusters
    all_cluster_guids = set()
    for cluster in clusters:
        all_cluster_guids.update(cluster.guids) 

    # Dictionary to store site-to-cluster mappings with domain-based keys
    sites = {}
    # Dictionary to track domain counters for creating domain_1, domain_2, etc.
    domain_counters = {}
    # Dictionary to map full URLs to their domain-based keys
    url_to_domain_key = {}
      
    # Function to search for HTML data with a specific GUID
    def search_html_data(html_data, site_url):
        unique_id = str(html_data.get("unique_id"))
        if unique_id in all_cluster_guids:
            try:
                for cluster in clusters:
                    if unique_id in cluster.guids:
                        cluster_id = int(cluster.id.split('_')[1]) + 1  # Extract the number from cluster_id and add 1
                        
                        # Create domain-based key if not already created
                        if site_url not in url_to_domain_key:
                            from urllib.parse import urlparse
                            try:
                                parsed_url = urlparse(site_url)
                                # Extract domain (remove www. if present)
                                domain = parsed_url.netloc.replace('www.', '') if site_url else 'unknown'
                                # Clean domain name for use as identifier (keep only alphanumeric and basic chars)
                                clean_domain = ''.join(c for c in domain if c.isalnum() or c in '-._').rstrip('.')
                                if not clean_domain:
                                    clean_domain = 'unknown'
                                
                                # Remove common domain suffixes for cleaner names
                                if '.' in clean_domain:
                                    domain_parts = clean_domain.split('.')
                                    # Take the main domain part (before first dot)
                                    main_domain = domain_parts[0]
                                else:
                                    main_domain = clean_domain
                                
                                # Initialize counter for this domain if not seen before
                                if main_domain not in domain_counters:
                                    domain_counters[main_domain] = 0
                                
                                # Increment counter and create domain-based key
                                domain_counters[main_domain] += 1
                                domain_key = f"{main_domain}_{domain_counters[main_domain]}"
                                
                                # Store the mapping
                                url_to_domain_key[site_url] = domain_key
                            except:
                                # Fallback in case of URL parsing errors
                                if 'unknown' not in domain_counters:
                                    domain_counters['unknown'] = 0
                                domain_counters['unknown'] += 1
                                domain_key = f"unknown_{domain_counters['unknown']}"
                                url_to_domain_key[site_url] = domain_key
                        
                        # Use the domain-based key
                        domain_key = url_to_domain_key[site_url]
                        
                        if domain_key not in sites:
                            sites[domain_key] = []
                        sites[domain_key].append(cluster_id)
                        if "clusters" not in html_data:
                            html_data["clusters"] = []
                        html_data["clusters"].append(cluster.__dict__)
                        break
            except Exception as e:
                print(f"An error occurred: {e}")
                data_to_return.append(f"An error occurred: {e}")
        for child in html_data.get("children", []):
            search_html_data(child, site_url)

    # Read the JSON file
    def find_latest_data_file(directory):
        search_pattern = os.path.join(directory, "data_*.json")
        files = glob.glob(search_pattern)
        if not files:
            return None
        latest_file = max(files, key=os.path.getmtime)
        return latest_file

    directory = os.path.join(PROJECT_ROOT, "backend", "api", "results")
    
    # Ensure the results directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created results directory: {directory}")
    
    file_path = find_latest_data_file(directory)

    # Check if the file exists
    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        file_read_start = time.time()
        with open(file_path, "r") as file:
            json_data = json.load(file)
            num_keys = len(json_data)
        file_read_time = time.time() - file_read_start
        
        print(f"File found: {file_path}")
        print(f"File size: {file_size} bytes")
        print(f"Number of top-level keys (GUIDs): {num_keys}")
        data_to_return.append(f"File found: {file_path}")
        data_to_return.append(f"File size: {file_size} bytes")
        data_to_return.append(f"Number of top-level keys (GUIDs): {num_keys}")
    else:
        if file_path is None:
            error_msg = f"No data files found in directory: {directory}"
            print(f"❌ {error_msg}")
            data_to_return.append(error_msg)
            return {"status": "error", "message": "No data files found. Please run URL processing first to generate data files.", "data": data_to_return}
        else:
            error_msg = f"File not found: {file_path}"
            print(f"❌ {error_msg}")
            data_to_return.append(error_msg)
            return {"status": "error", "message": "Data file not found", "data": data_to_return}

    # Process the JSON data
    guid_processing_start = time.time()
    processed_guids = 0
    for key, guid_data in json_data.items():
        html_data = guid_data.get("html_data")
        if html_data:
            site_url = guid_data.get('url', '')
            print(f"Processing GUID: {key} for URL: {site_url}")
            data_to_return.append(f"Processing GUID: {key} for URL: {site_url}")
            search_html_data(html_data, site_url)
            processed_guids += 1
        if "combinations_by_level" in guid_data:
            guid_data.pop("combinations_by_level")
    guid_processing_time = time.time() - guid_processing_start

    cluster_timing_logs["steps"]["guid_processing"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Processing GUIDs and creating site mappings",
        "total_guids": len(all_cluster_guids),
        "sites_found": len(sites),
        "file_size_bytes": file_size if os.path.exists(file_path) else 0,
        "file_size_mb": (file_size / (1024 * 1024)) if os.path.exists(file_path) else 0,
        "guid_count": num_keys if os.path.exists(file_path) else 0,
        "processed_guids": processed_guids,
        "file_operations": {
            "file_read": {
                "duration": file_read_time,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024)
            },
            "guid_processing": {
                "duration": guid_processing_time,
                "guids_processed": processed_guids,
                "processing_rate": processed_guids / guid_processing_time if guid_processing_time > 0 else 0
            }
        }
    }

    # Format sites as a string object with domain-based keys
    sites_str = "sites = {\n"
    for domain_key, cluster_ids in sites.items():
        sites_str += f"    '{domain_key}': {cluster_ids},\n"
    sites_str += "}"
    
    # Format URL to domain mapping for reference
    url_mapping_str = "\n# URL to Domain Key Mapping:\n"
    for url, domain_key in url_to_domain_key.items():
        url_mapping_str += f"# {domain_key}: {url}\n"
    
    # Print the sites mapping and URL mapping
    print("\n" + sites_str)
    print(url_mapping_str)
    data_to_return.append(sites_str)
    data_to_return.append(url_mapping_str)
    
    # Step 2.5: Compute site similarity analysis with proper error handling
    similarity_step_start = time.time()
    
    try:
        sim_combined = compute_site_cosine_similarity(sites)
        print(f"sim_combined result: {sim_combined}")
        
        # Create the formatted site similarity result object
        if sim_combined.empty:
            site_similarity_result = {
                "status": "success",
                "message": "No sites data provided",
                "data": {
                    "matrix": {},
                    "sites": [],
                    "raw_matrix": [],
                    "summary": {
                        "total_sites": 0,
                        "average_similarity": 0,
                        "max_similarity": 0,
                        "min_similarity": 0
                    }
                }
            }
        else:
            n = len(sim_combined.index)
            
            # Calculate summary statistics
            if n == 0:
                average_similarity = max_similarity = min_similarity = 0.0
            elif n == 1:
                average_similarity = max_similarity = min_similarity = 100.0
            else:
                # Multiple sites case - compute from upper triangular matrix (excluding diagonal)
                upper_triangle_values = sim_combined.values[np.triu_indices(n, k=1)]
                
                if len(upper_triangle_values) == 0:
                    average_similarity = max_similarity = min_similarity = 100.0
                else:
                    average_similarity = np.mean(upper_triangle_values)
                    max_similarity = np.max(upper_triangle_values)
                    min_similarity = np.min(upper_triangle_values)
            
            site_similarity_result = {
                "status": "success",
                "message": f"Role vector-based cosine similarity computed for {n} sites",
                "data": {
                    "matrix": sim_combined.to_dict(),
                    "sites": list(sim_combined.index),
                    "raw_matrix": sim_combined.values.tolist(),
                    "summary": {
                        "total_sites": n,
                        "average_similarity": float(average_similarity),
                        "max_similarity": float(max_similarity),
                        "min_similarity": float(min_similarity)
                    }
                }
            }
    except Exception as e:
        import traceback
        site_similarity_result = {
            "status": "error",
            "message": f"Error computing site similarity: {str(e)}",
            "data": None,
            "traceback": traceback.format_exc()
        }
        print(f"Site similarity error: {str(e)}")
    
    similarity_step_time = time.time() - similarity_step_start
    
    cluster_timing_logs["steps"]["site_similarity_analysis"] = {
        "start_time": similarity_step_start,
        "end_time": time.time(),
        "duration": similarity_step_time,
        "description": "Computing cosine similarity between sites",
        "sites_analyzed": len(sites),
        "success": site_similarity_result["status"] == "success"
    }
    
    print(f"\033[94m=== SITE SIMILARITY ANALYSIS ===\033[0m")
    if site_similarity_result["status"] == "success":
        print(f"\033[92mSite similarity analysis completed successfully\033[0m")
        print(f"\033[93mSites analyzed: {site_similarity_result['data']['summary']['total_sites']}\033[0m")
        print(f"\033[93mAverage similarity: {site_similarity_result['data']['summary']['average_similarity']:.2f}%\033[0m")
        data_to_return.append(f"Site similarity analysis completed for {site_similarity_result['data']['summary']['total_sites']} sites")
    else:
        print(f"\033[91mSite similarity analysis failed: {site_similarity_result['message']}\033[0m")
        data_to_return.append(f"Site similarity analysis failed: {site_similarity_result['message']}")
    print(f"\033[94m=== END SITE SIMILARITY ANALYSIS ===\033[0m\n")

    # List of valid CSS properties
    VALID_CSS_PROPERTIES = [
        # Fonts and Text
        "font-family", "font-size", "font-weight", "font-style", "font-variant", 
        "font-size-adjust", "font-stretch", "font-feature-settings", "color", 
        "text-align", "text-decoration", "text-transform", "text-shadow", 
        "letter-spacing", "line-height", "white-space", "word-spacing", 
        "word-wrap", "word-break", "overflow-wrap", "hyphens", "direction",

        # Backgrounds and Borders
        "background-color", "background-image", "background-position", 
        "background-repeat", "background-size", "background-attachment", 
        "border", "border-width", "border-style", "border-color", 
        "border-top", "border-right", "border-bottom", "border-left", 
        "border-radius", "border-collapse", "box-shadow", "outline", 
        "outline-color", "outline-style", "outline-width",

        # Margins and Padding
        "margin", "margin-top", "margin-right", "margin-bottom", "margin-left", 
        "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",

        # # Display and Positioning
        # "display", "position", "top", "right", "bottom", "left", "z-index", 
        # "float", "clear", "visibility", "overflow", "overflow-x", "overflow-y", 
        # "clip", "vertical-align",

        # # Flexbox
        # "flex", "flex-grow", "flex-shrink", "flex-basis", "flex-direction", 
        # "flex-wrap", "align-items", "align-content", "justify-content", 
        # "order", "align-self",

        # # Grid
        # "grid", "grid-template-columns", "grid-template-rows", 
        # "grid-template-areas", "grid-column", "grid-row", "grid-gap", 
        # "grid-auto-columns", "grid-auto-rows", "grid-column-start", 
        # "grid-column-end", "grid-row-start", "grid-row-end", 
        # "place-items", "place-content", "place-self",

        # # Sizing
        # "width", "height", "min-width", "min-height", "max-width", "max-height",

        # # Animations and Transitions
        # "animation", "animation-name", "animation-duration", 
        # "animation-timing-function", "animation-delay", "animation-iteration-count", 
        # "animation-direction", "animation-fill-mode", "transition", 
        # "transition-property", "transition-duration", "transition-timing-function", 
        # "transition-delay",

        # # Transforms
        # "transform", "transform-origin", "transform-style", "perspective", 
        # "perspective-origin",

        # # Columns
        # "columns", "column-width", "column-count", "column-gap", 
        # "column-rule", "column-rule-width", "column-rule-style", "column-rule-color",

        # # Tables
        # "table-layout", "border-spacing", "border-collapse", "caption-side", 
        # "empty-cells",

        # # Lists
        # "list-style", "list-style-type", "list-style-position", "list-style-image",

        # # Content and Cursor
        # "content", "quotes", "cursor", "caret-color",

        # # Misc
        # "opacity", "visibility", "pointer-events", "filter", "resize", 
        # "user-select", "will-change", "zoom",

        # Vendor-specific prefixes
        # "-webkit-transform", "-webkit-transition", "-webkit-animation", 
        # "-webkit-box-shadow", "-webkit-border-radius", "-webkit-opacity", 
        # "-webkit-flex", "-webkit-align-items", "-webkit-justify-content", 
        # "-webkit-align-self", "-webkit-order", "-webkit-flex-grow", 
        # "-webkit-flex-shrink", "-webkit-flex-basis", "-webkit-perspective", 
        # "-webkit-perspective-origin", "-webkit-backface-visibility", 
        # "-webkit-box-sizing", "-webkit-text-fill-color", "-webkit-text-stroke", 
        # "-webkit-text-stroke-width", "-webkit-appearance", "-webkit-mask", 
        # "-webkit-mask-image", "-webkit-mask-position", "-webkit-mask-size", 
        # "-webkit-mask-repeat", "-webkit-mask-clip", "-webkit-mask-origin", 
        # "-webkit-mask-composite", "-webkit-box-flex", "-webkit-box-align", 
        # "-webkit-box-pack", "-webkit-box-orient", "-webkit-box-direction", 
        # "-webkit-box-decoration-break", "-webkit-background-clip", 
        # "-webkit-filter", "-webkit-hyphens", "-webkit-overflow-scrolling", 
        # "-webkit-tap-highlight-color", "-webkit-touch-callout", 
        # "-webkit-writing-mode", "-webkit-transition-timing-function", 
        # "-webkit-transition-duration", "-webkit-transition-property", 
        # "-webkit-transition-delay", "-webkit-animation-delay", 
        # "-webkit-animation-duration", "-webkit-animation-iteration-count", 
        # "-webkit-animation-timing-function", "-webkit-animation-name"
        
        # Text Decoration Properties
				"text-decoration-style",
				"text-decoration-color",
				# "text-decoration-thickness",
				# "text-decoration-skip-ink",
				# "text-decoration-skip-ink-adjust",
				# "text-decoration-skip-ink-adjust-mode",
				# "text-decoration-skip-ink-adjust-mode-adjustment"
    ]
    
    def escape_quotes(value):
        if not isinstance(value, str):
            value = str(value)
        return value.replace('"', "'")
    
    # Step 3: HTML file generation
    step_start = time.time()
    def create_html_from_json(json_data, output_dir, level_info=None):
        created_files = []  # Track created files
        total_html_size = 0
        files_created = 0
        
        def create_element(element_data):
            unique_id = element_data.get("unique_id", None)
            tag_name = element_data.get("tag_name", "div")
            text = element_data.get("actual_text", "")
            children = element_data.get("children", [])
            attributes = element_data.get("attributes", {})
            clusters = element_data.get("clusters", [])
            
            #remove from attributes start with -webkit
            attributes = {key: value for key, value in attributes.items() if not key.startswith("-webkit")}
            
            # Separate CSS styles from other attributes
            styles = {key: value for key, value in attributes.items() if key in VALID_CSS_PROPERTIES}
            other_attributes = {key: value for key, value in attributes.items() if key not in VALID_CSS_PROPERTIES}
    
            # Convert styles dictionary to a string of valid CSS styles
            style_str = "; ".join(f'{key}: {escape_quotes(value)}' for key, value in styles.items())
            if(len(clusters) > 0):
                for cluster in clusters:                    
                    style_str += f"; background-color: {cluster['color']}"
    
            # Convert other attributes dictionary to a string of HTML attributes
            attributes_str = " ".join(
                f'{key}="{escape_quotes(value)}"' for key, value in other_attributes.items()
            )
            
            if(len(clusters) > 0):
                for cluster in clusters:
                    attributes_str += f' data-cluster="{cluster["id"]}"'
            
            children_html = "".join(create_element(child) for child in children)
            
            if(len(clusters) == 0):
                return f'<{tag_name}">{children_html}</{tag_name}>'
            return f'<{tag_name} style="{style_str}"  {attributes_str}>{text}{children_html}</{tag_name}>'
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for key, guid_data in json_data.items():
            html_data = guid_data.get("html_data", {})
            html_content = create_element(html_data)
            
            # Get URL and create better filename with full path information
            url = guid_data.get('url', '')
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.replace('www.', '') if url else 'unknown'
                # Clean domain for filename (remove special characters)
                clean_domain = ''.join(c for c in domain if c.isalnum() or c in '-._').rstrip('.')
                
                # Extract meaningful path information
                path = parsed_url.path.strip('/')
                if path:
                    # Take the last meaningful part of the path (like article slug)
                    path_parts = path.split('/')
                    # Get the last non-empty part, or combine last 2 parts if short
                    if len(path_parts) >= 2 and len(path_parts[-1]) < 10:
                        url_identifier = '_'.join(path_parts[-2:])
                    else:
                        url_identifier = path_parts[-1] if path_parts[-1] else path_parts[-2] if len(path_parts) > 1 else 'page'
                    
                    # Clean the URL identifier (keep only safe characters)
                    url_identifier = ''.join(c for c in url_identifier if c.isalnum() or c in '-_')[:50]  # Limit length
                else:
                    url_identifier = 'home'
            except:
                clean_domain = 'unknown'
                url_identifier = 'page'
            
            # Use the FULL GUID - this is the key fix!
            full_guid = key  # This is the complete GUID
            short_id = key[:8] if len(key) >= 8 else key  # Only for display in title
            
            # Create level-specific directory
            level_str = f"level_{level_info}" if level_info else "unknown_level"
            level_dir = os.path.join(output_dir, level_str)
            if not os.path.exists(level_dir):
                os.makedirs(level_dir)
            
            # Create descriptive filename: level_domain_urlidentifier_fullguid.html
            if clean_domain and clean_domain != 'unknown':
                filename = f"{level_str}_{clean_domain}_{url_identifier}_{full_guid}.html"
            else:
                filename = f"{level_str}_{url_identifier}_{full_guid}.html"
                
            # Add page title for better HTML structure with URL identifier
            if url_identifier and url_identifier != 'page' and url_identifier != 'home':
                page_title = f"Level {level_info} - {domain}/{url_identifier} ({short_id})" if level_info else f"{domain}/{url_identifier} ({short_id})"
            else:
                page_title = f"Level {level_info} - {domain} ({short_id})" if level_info else f"{domain} ({short_id})"
            final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .header {{ background: #f5f5f5; padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
        .info {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{page_title}</h2>
        <div class="info">
            <strong>URL:</strong> {url}<br>
            <strong>GUID:</strong> {key}<br>
            <strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    <div class="content">
        {html_content}
    </div>
</body>
</html>"""
            
            output_file = os.path.join(level_dir, filename)
            
            file_write_start = time.time()
            with open(output_file, "w", encoding='utf-8') as file:
                file.write(final_html)
            file_write_time = time.time() - file_write_start
            
            # Get file size
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            total_html_size += file_size
            files_created += 1
            
            print(f"File created: {output_file}")
            # Store relative path from output_html_files directory for web serving
            relative_path = os.path.join(level_str, filename)
            created_files.append({
                'filename': filename,
                'path': relative_path,  # Remove the "output_html_files/" prefix
                'full_path': output_file,
                'file_size_bytes': file_size,
                'file_size_kb': file_size / 1024,
                'write_time': file_write_time,
                'level': level_info,
                'domain': domain,
                'clean_domain': clean_domain,
                'url_identifier': url_identifier,
                'short_id': short_id,
                'full_guid': full_guid,
                'url': url,
                'title': page_title,
                'guid': key
            })
            data_to_return.append(f"File created: {os.path.abspath(output_file)}")

        return created_files, total_html_size, files_created

    # Create HTML files and get the list of created files
    html_creation_start = time.time()
    output_html_dir = os.path.join(PROJECT_ROOT, "output_html_files")
    created_html_files, total_html_size, files_created = create_html_from_json(json_data, output_html_dir, level_info)
    html_creation_time = time.time() - html_creation_start
    
    cluster_timing_logs["steps"]["html_generation"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Generating HTML files from processed data",
        "html_files_created": len(created_html_files),
        "total_html_size_bytes": total_html_size,
        "total_html_size_mb": total_html_size / (1024 * 1024),
        "average_file_size_bytes": total_html_size / len(created_html_files) if created_html_files else 0,
        "average_file_size_kb": (total_html_size / len(created_html_files)) / 1024 if created_html_files else 0,
        "html_creation_time": html_creation_time,
        "files_per_second": len(created_html_files) / html_creation_time if html_creation_time > 0 else 0,
        "bytes_per_second": total_html_size / html_creation_time if html_creation_time > 0 else 0
    }
        
    # Step 4: Results file writing
    step_start = time.time()
    # Write results to a file
    output_file_path = os.path.join(PROJECT_ROOT, "backend", "api", "results", "WEB.json")
    
    # Get file size before writing
    file_size_before = os.path.getsize(output_file_path) if os.path.exists(output_file_path) else 0
    
    file_write_start = time.time()
    with open(output_file_path, "w") as file:
        json.dump(json_data, file, indent=4)
    file_write_time = time.time() - file_write_start
    
    # Get file size after writing
    file_size_after = os.path.getsize(output_file_path) if os.path.exists(output_file_path) else 0

    print(f"Results written to: {output_file_path}")
    data_to_return.append(f"Results written to: {output_file_path}")
    
    cluster_timing_logs["steps"]["results_writing"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Writing final results to WEB.json file",
        "file_path": output_file_path,
        "file_size_before_bytes": file_size_before,
        "file_size_after_bytes": file_size_after,
        "file_size_change_bytes": file_size_after - file_size_before,
        "file_size_mb": file_size_after / (1024 * 1024),
        "file_write_time": file_write_time,
        "write_speed_mb_per_second": (file_size_after / (1024 * 1024)) / file_write_time if file_write_time > 0 else 0
    }

    # Calculate total processing time
    cluster_timing_logs["end_time"] = time.time()
    cluster_timing_logs["total_duration"] = cluster_timing_logs["end_time"] - cluster_timing_logs["start_time"]

    return {
        "status": "success", 
        "message": "Clustering completed successfully", 
        "data": json.dumps(data_to_return),
        "sites": sites,
        "html_files": created_html_files,  # Return the list of created HTML files
        "timing_logs": cluster_timing_logs,  # Add timing logs to the response
        "site_similarity": site_similarity_result  # Add site similarity results
    }

def process_urls_from_api(urls, levels, mode=0):
    try:
        # Clean up directories only at the start of the API call
        # But preserve data files for reuse functionality
        results_dir = os.path.join(PROJECT_ROOT, "backend", "api", "results")
        output_html_dir = os.path.join(PROJECT_ROOT, "output_html_files")
        
        # Ensure results directory exists
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            print(f"📁 Created results directory: {results_dir}")
        
        # Clean up results directory (but keep recent data files for reuse)
        if os.path.exists(results_dir):
            import time as time_module
            current_time = time_module.time()
            for file in os.listdir(results_dir):
                file_path = os.path.join(results_dir, file)
                try:
                    if os.path.isfile(file_path):
                        # Keep recent data files (less than 5 minutes old) for reuse
                        if file.startswith("data_") and file.endswith(".json"):
                            file_age = current_time - os.path.getmtime(file_path)
                            if file_age < 300:  # Keep files less than 5 minutes old
                                print(f"Keeping recent data file: {file} (age: {file_age:.1f}s)")
                                continue
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        # Ensure output_html_files directory exists  
        if not os.path.exists(output_html_dir):
            os.makedirs(output_html_dir)
            print(f"📁 Created output directory: {output_html_dir}")
        
        # Clean up output_html_files directory
        if os.path.exists(output_html_dir):
            for file in os.listdir(output_html_dir):
                file_path = os.path.join(output_html_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

        if mode == 0:
            # Original behavior - process all URLs together
            result = process_urls_from_cli(urls, levels, from_api=True)
            return {
                "status": result.get("status"), 
                "message": result.get("message"), 
                "body": result.get("data", {}),
                "clustering_results": result.get("clustering_results", {}),
                "processed_clusters": result.get("processed_clusters", {}),
                "html_files": result.get("html_files", []),  # Use tracked HTML files
                "timing_logs": result.get("timing_logs", {}),  # Include timing logs
                "best_level_info": result.get("best_level_info")  # Add missing best level info
            }
        else:
            # Mode 1 - process URLs by domain with enhanced cache checking
            from urllib.parse import urlparse
            
            print(f"\033[94m🌐 MODE 1: Starting domain-based processing\033[0m")
            
            # Group URLs by domain
            domain_groups = {}
            for url in urls:
                try:
                    domain = urlparse(url).hostname or 'unknown'
                    if domain not in domain_groups:
                        domain_groups[domain] = []
                    domain_groups[domain].append(url)
                except Exception as e:
                    print(f"\033[91m❌ Error parsing URL {url}: {e}\033[0m")
                    if 'unknown' not in domain_groups:
                        domain_groups['unknown'] = []
                    domain_groups['unknown'].append(url)
            
            print(f"\033[94m📊 Grouped into {len(domain_groups)} domains: {list(domain_groups.keys())}\033[0m")
            
            # Process each domain group separately with enhanced cache reporting
            all_results = {
                "status": "success",
                "message": "URLs processed successfully by domain",
                "domain_results": [],
                "timing_logs": {
                    "total_start_time": time.time(),
                    "steps": {},
                    "performance_metrics": {}
                }
            }
            
            total_cache_hits = 0
            total_urls_processed = 0
            
            # Calculate total URLs consistently
            expected_total_urls = len(urls)
            
            for domain_index, (domain, domain_urls) in enumerate(domain_groups.items(), 1):
                print(f"\033[96m🔄 Processing domain {domain_index}/{len(domain_groups)}: {domain} ({len(domain_urls)} URLs)\033[0m")
                
                try:
                    domain_result = process_urls_from_cli(domain_urls, levels, from_api=True)
                    
                    # Extract cache metrics from domain result
                    domain_cache_hits = 0
                    domain_urls_count = len(domain_urls)
                    
                    if domain_result.get('timing_logs') and domain_result['timing_logs'].get('performance_metrics'):
                        metrics = domain_result['timing_logs']['performance_metrics']
                        domain_cache_hits = metrics.get('urls_from_cache', 0)
                        total_cache_hits += domain_cache_hits
                        total_urls_processed += domain_urls_count
                        
                        print(f"\033[92m✅ Domain {domain}: {domain_cache_hits}/{domain_urls_count} URLs from cache ({(domain_cache_hits/domain_urls_count)*100:.1f}%)\033[0m")
                    
                    # Find best clustering level for this domain
                    domain_clustering_results = domain_result.get("clustering_results", [])
                    domain_best_level_info = find_best_clustering_level(domain_clustering_results)
                    
                    if domain_best_level_info:
                        print(f"\033[93m🏆 DOMAIN {domain} - BEST LEVEL: Level {domain_best_level_info['best_level']}\033[0m")
                        print(f"\033[93m   📊 {domain_best_level_info['algorithm_details']['selection_reason']}\033[0m")
                        
                        # Mark the best level in domain clustering results
                        for result in domain_clustering_results:
                            if result.get('level') == domain_best_level_info['best_level']:
                                result['is_best_level'] = True
                                result['best_level_details'] = domain_best_level_info['algorithm_details']
                        
                        # Mark the best level in domain processed clusters
                        domain_processed_clusters = domain_result.get("processed_clusters", [])
                        for processed_cluster in domain_processed_clusters:
                            if processed_cluster.get('level') == domain_best_level_info['best_level']:
                                processed_cluster['is_best_level'] = True
                                processed_cluster['best_level_details'] = domain_best_level_info['algorithm_details']
                    else:
                        print(f"\033[94m📊 Domain {domain}: No best clustering level detected\033[0m")
                    
                    all_results["domain_results"].append({
                        "domain": domain,
                        "urls": domain_urls,
                        "status": domain_result.get("status"),
                        "message": domain_result.get("message"),
                        "clustering_results": domain_result.get("clustering_results", {}),
                        "processed_clusters": domain_result.get("processed_clusters", {}),
                        "html_files": domain_result.get("html_files", []),  # Use tracked HTML files
                        "timing_logs": domain_result.get("timing_logs", {}),  # Include timing logs
                        "best_level_info": domain_best_level_info  # Add best level info for this domain
                    })
                except Exception as e:
                    print(f"\033[91m❌ Domain {domain} failed: {str(e)}\033[0m")
                    all_results["domain_results"].append({
                        "domain": domain,
                        "urls": domain_urls,
                        "status": "error",
                        "message": str(e)
                    })
            
            # Calculate overall metrics for Mode 1
            all_results["timing_logs"]["total_end_time"] = time.time()
            all_results["timing_logs"]["total_duration"] = all_results["timing_logs"]["total_end_time"] - all_results["timing_logs"]["total_start_time"]
            
            overall_cache_efficiency = (total_cache_hits / total_urls_processed * 100) if total_urls_processed > 0 else 0
            
            all_results["timing_logs"]["performance_metrics"] = {
                "total_processing_time": all_results["timing_logs"]["total_duration"],
                "mode": 1,
                "domains_processed": len(domain_groups),
                "total_urls": total_urls_processed,
                "urls_from_cache": total_cache_hits,
                "urls_newly_processed": total_urls_processed - total_cache_hits,
                "cache_efficiency_percent": overall_cache_efficiency,
                "cache_savings": f"Saved processing {total_cache_hits}/{total_urls_processed} URLs ({overall_cache_efficiency:.1f}%)",
                "domains": list(domain_groups.keys())
            }
            
            # Find overall best clustering level across all domains for Mode 1
            all_clustering_results = []
            for domain_result in all_results["domain_results"]:
                if domain_result.get("status") == "success" and domain_result.get("clustering_results"):
                    for cluster_result in domain_result["clustering_results"]:
                        # Add domain context to clustering result for overall analysis
                        cluster_result_copy = cluster_result.copy()
                        cluster_result_copy["domain"] = domain_result["domain"]
                        all_clustering_results.append(cluster_result_copy)
            
            overall_best_level_info = find_best_clustering_level(all_clustering_results)
            if overall_best_level_info:
                print(f"\033[93m🏆 MODE 1 OVERALL BEST LEVEL: Level {overall_best_level_info['best_level']} (across all domains)\033[0m")
                print(f"\033[93m   📊 {overall_best_level_info['algorithm_details']['selection_reason']}\033[0m")
                all_results["best_level_info"] = overall_best_level_info
            else:
                print(f"\033[94m📊 MODE 1: No overall best clustering level detected across domains\033[0m")
                all_results["best_level_info"] = None
            
            # Add test metadata for frontend compatibility
            all_results["test_metadata"] = {
                "mode": mode,
                "levels": levels,
                "url_count": len(urls),
                "urls": urls,
                "duration": all_results["timing_logs"]["total_duration"]
            }
            
            if ENABLE_CACHING:
                if total_cache_hits > 0:
                    print(f"\033[92m💾 MODE 1 CACHING ENABLED: Saved processing {total_cache_hits}/{total_urls_processed} URLs ({overall_cache_efficiency:.1f}% cache efficiency)\033[0m")
                else:
                    print(f"\033[94m💾 MODE 1 CACHING ENABLED: No cache hits this run - processed all {total_urls_processed} URLs fresh\033[0m")
            else:
                print(f"\033[93m🚫 MODE 1 CACHING DISABLED: Processed all {total_urls_processed} URLs fresh - no cache savings\033[0m")
            
            return all_results
            
    except Exception as e:
        error_message = f"Error processing URLs: {str(e)}"
        stack_trace = traceback.format_exc()
        with open('error.log', 'a') as error_file:
            error_file.write(f"{error_message}\n")
            error_file.write(f"{stack_trace}\n")
        return {
            "status": "error", 
            "message": str(e),
            "stack_trace": stack_trace
        }


def process_clusters_from_api(clusters_data):
    try:
        result = process_clusters_from_cli(clusters_data, from_api=True)
        
        return {
            "status": result.get("status"), 
            "message": result.get("message"), 
            "body": result.get("data", {}),
            "timing_logs": result.get("timing_logs", {})  # Include timing logs
        }
    except Exception as e:
        error_message = f"Error processing clusters: {str(e)}"
        stack_trace = traceback.format_exc()
        with open('error.log', 'a') as error_file:
            error_file.write(f"{error_message}\n")
            error_file.write(f"{stack_trace}\n")
        return {
            "status": "error", 
            "message": str(e),
            "stack_trace": stack_trace
        }

def find_best_clustering_level(clustering_results):
    """
    Find the best clustering level using median-based algorithm.
    
    Algorithm:
    1. Collect all cluster counts from all levels
    2. Find median of cluster counts  
    3. Order levels by cluster count (smallest to largest)
    4. Take the level at median position (Y)
    5. Get cluster count at that position (W)
    6. Filter results with W clusters or fewer
    7. Return the level with highest DBCV score from filtered results
    
    Args:
        clustering_results: List of clustering result dictionaries
        
    Returns:
        dict: Contains best_level and algorithm details, or None if no valid results
    """
    if not clustering_results:
        return None
    
    # Step 1: Collect all successful clustering results
    valid_results = []
    for result in clustering_results:
        if result.get('status') != 'error':
            # Handle both lightweight and full cluster info structures
            cluster_info = None
            if result.get('cluster_info'):
                cluster_info = result['cluster_info']
            elif result.get('cluster_summary'):
                cluster_info = result['cluster_summary']
            
            if cluster_info:
                num_clusters = cluster_info.get('num_clusters', 0)
                dbcv_score = cluster_info.get('dbcv_score', 0)
                
                # Only include results with valid clustering (more than 0 clusters and positive DBCV)
                if num_clusters > 0 and dbcv_score > 0:
                    valid_results.append({
                        'level': result.get('level'),
                        'num_clusters': num_clusters,
                        'dbcv_score': dbcv_score,
                        'result': result
                    })
    
    if len(valid_results) < 2:  # Need at least 2 valid results for meaningful comparison
        return None
    
    # Step 2: Find median of cluster counts
    cluster_counts = [r['num_clusters'] for r in valid_results]
    cluster_counts_sorted = sorted(cluster_counts)
    n = len(cluster_counts_sorted)
    
    if n % 2 == 0:
        median_clusters = (cluster_counts_sorted[n//2 - 1] + cluster_counts_sorted[n//2]) / 2
    else:
        median_clusters = cluster_counts_sorted[n//2]
    
    # Step 3: Order levels by cluster count (smallest to largest)
    valid_results.sort(key=lambda x: x['num_clusters'])
    
    # Step 4: Take level at median position (Y)
    median_position = n // 2
    w_cluster_count = valid_results[median_position]['num_clusters']
    
    # Step 5: Filter results with W clusters or fewer
    filtered_results = [r for r in valid_results if r['num_clusters'] <= w_cluster_count]
    
    # Step 6: Return the level with highest DBCV score from filtered results
    if filtered_results:
        best_result = max(filtered_results, key=lambda x: x['dbcv_score'])
        
        return {
            'best_level': best_result['level'],
            'best_num_clusters': best_result['num_clusters'],
            'best_dbcv_score': best_result['dbcv_score'],
            'algorithm_details': {
                'total_valid_levels': len(valid_results),
                'median_clusters': median_clusters,
                'median_position': median_position,
                'w_cluster_count': w_cluster_count,
                'filtered_candidates': len(filtered_results),
                'all_cluster_counts': cluster_counts,
                'selection_reason': f"Selected level {best_result['level']} with {best_result['num_clusters']} clusters (≤{w_cluster_count}) and highest DBCV score {best_result['dbcv_score']:.3f}"
            }
        }
    
    return None

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--urls', type=str, required=True, help='Comma-separated list of URLs')
    parser.add_argument('--levels', type=int, nargs='+', required=True, help='Space-separated list of levels')
    args = parser.parse_args()

    # Convert the comma-separated string of URLs into a list
    urls = args.urls.split(',')

    # Get the levels from the arguments
    levels = args.levels

    process_urls_from_cli(urls, levels)