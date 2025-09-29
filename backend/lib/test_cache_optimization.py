#!/usr/bin/env python3
"""
Automated Cache Optimization Testing Script

This script automatically tests the cache optimization system using predefined URLs
to demonstrate the cache efficiency improvements.
"""

import sys
import os
import time
import json

# Add the current directory to the path to import lib
sys.path.append(os.path.dirname(__file__))

from lib import process_urls_from_cli
from test_urls_examples import get_progressive_test_sequence, GITHUB_URLS, STACKOVERFLOW_URLS, MDN_URLS

def run_cache_test(urls, levels, test_name, step_number=None):
    """Run a single cache test and return the results."""
    print(f"\n{'='*60}")
    if step_number:
        print(f"🧪 STEP {step_number}: {test_name}")
    else:
        print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")
    print(f"📋 URLs ({len(urls)}):")
    for i, url in enumerate(urls, 1):
        print(f"   {i}. {url}")
    print(f"📊 Levels: {levels}")
    print(f"\n🚀 Running test...")
    
    start_time = time.time()
    
    try:
        # Run the URL processing
        result = process_urls_from_cli(urls, levels, from_api=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Extract cache efficiency from timing logs
        cache_efficiency = "N/A"
        urls_from_cache = 0
        total_urls = len(urls)
        
        if result.get('timing_logs') and result['timing_logs'].get('performance_metrics'):
            metrics = result['timing_logs']['performance_metrics']
            if 'cache_efficiency_percent' in metrics:
                cache_efficiency = f"{metrics['cache_efficiency_percent']:.1f}%"
            if 'urls_from_cache' in metrics:
                urls_from_cache = metrics['urls_from_cache']
        
        print(f"\n✅ TEST COMPLETED SUCCESSFULLY")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🎯 Cache Efficiency: {cache_efficiency}")
        print(f"📊 URLs from Cache: {urls_from_cache}/{total_urls}")
        print(f"🔄 URLs Processed: {total_urls - urls_from_cache}/{total_urls}")
        
        return {
            'success': True,
            'duration': duration,
            'cache_efficiency': cache_efficiency,
            'urls_from_cache': urls_from_cache,
            'total_urls': total_urls,
            'result': result
        }
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'duration': time.time() - start_time
        }

def run_progressive_cache_test():
    """Run the complete progressive cache test sequence."""
    print("🚀 STARTING PROGRESSIVE CACHE OPTIMIZATION TEST")
    print("=" * 60)
    print("This test demonstrates how the cache system builds up and improves efficiency over time.")
    print("Each step will show increasing cache hit rates as the cache grows.")
    
    # Test configuration
    levels = [1, 2]  # Test with levels 1 and 2
    
    # Get the progressive test sequence
    test_sequence = get_progressive_test_sequence()
    
    results = []
    
    for step in test_sequence:
        result = run_cache_test(
            urls=step['urls'],
            levels=levels,
            test_name=step['name'],
            step_number=step['step']
        )
        
        result['step_info'] = step
        results.append(result)
        
        # Pause between tests to see results clearly
        print(f"\n⏸️  Pausing for 2 seconds before next test...")
        time.sleep(2)
    
    # Summary
    print(f"\n📊 PROGRESSIVE TEST SUMMARY")
    print("=" * 60)
    
    for i, result in enumerate(results):
        step_info = result['step_info']
        status = "✅" if result['success'] else "❌"
        cache_eff = result.get('cache_efficiency', 'N/A')
        duration = result.get('duration', 0)
        
        print(f"{status} Step {step_info['step']}: {step_info['name']}")
        print(f"   Cache Efficiency: {cache_eff} | Duration: {duration:.2f}s")
        print(f"   Expected: {step_info['expected_cache']}")
        
    return results

def run_domain_comparison_test():
    """Test cache efficiency with different domain combinations."""
    print(f"\n🌐 DOMAIN COMPARISON TEST")
    print("=" * 60)
    print("This test compares cache efficiency between single-domain and multi-domain requests.")
    
    levels = [1, 2]
    results = []
    
    # Test 1: Single domain (GitHub only)
    result1 = run_cache_test(
        urls=GITHUB_URLS,
        levels=levels,
        test_name="Single Domain Test (GitHub)"
    )
    results.append(('Single Domain', result1))
    
    time.sleep(2)
    
    # Test 2: Multi-domain (mixed)
    mixed_urls = [GITHUB_URLS[0], STACKOVERFLOW_URLS[0], MDN_URLS[0]]
    result2 = run_cache_test(
        urls=mixed_urls,
        levels=levels,
        test_name="Multi-Domain Test (Mixed)"
    )
    results.append(('Multi-Domain', result2))
    
    time.sleep(2)
    
    # Test 3: Rerun single domain (should be cached)
    result3 = run_cache_test(
        urls=GITHUB_URLS,
        levels=levels,
        test_name="Single Domain Rerun (Cache Test)"
    )
    results.append(('Single Domain Rerun', result3))
    
    # Summary
    print(f"\n📊 DOMAIN COMPARISON SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅" if result['success'] else "❌"
        cache_eff = result.get('cache_efficiency', 'N/A')
        duration = result.get('duration', 0)
        
        print(f"{status} {test_name}:")
        print(f"   Cache Efficiency: {cache_eff} | Duration: {duration:.2f}s")
    
    return results

def main():
    """Main function to run cache optimization tests."""
    print("🧪 CACHE OPTIMIZATION TESTING SUITE")
    print("=" * 60)
    print("This script will test the cache optimization system using predefined URLs.")
    print("You can run different test types to see how the cache improves performance.")
    print("")
    
    while True:
        print("Available tests:")
        print("1. 🚀 Progressive Cache Test (Recommended)")
        print("2. 🌐 Domain Comparison Test")
        print("3. 📊 Show Test URLs")
        print("4. 🚪 Exit")
        
        choice = input("\nSelect a test (1-4): ").strip()
        
        if choice == "1":
            run_progressive_cache_test()
        elif choice == "2":
            run_domain_comparison_test()
        elif choice == "3":
            os.system("python test_urls_examples.py")
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-4.")
        
        input("\n⏸️  Press Enter to continue...")

if __name__ == "__main__":
    main() 