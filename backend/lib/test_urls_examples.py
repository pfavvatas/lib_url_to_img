#!/usr/bin/env python3
"""
Test URLs for Cache Optimization Testing

This file contains reliable URLs from different domains that can be used
consistently for testing the cache system without hitting random domains.
"""

# ============================================================================
# DOMAIN 1: GitHub (Developer/Tech Content)
# ============================================================================
GITHUB_URLS = [
    "https://github.com/features",
    "https://github.com/pricing", 
    "https://github.com/enterprise"
]

# ============================================================================
# DOMAIN 2: Stack Overflow (Technical Q&A)
# ============================================================================
STACKOVERFLOW_URLS = [
    "https://stackoverflow.com/questions",
    "https://stackoverflow.com/tags",
    "https://stackoverflow.com/help"
]

# ============================================================================
# DOMAIN 3: Mozilla MDN (Web Documentation)
# ============================================================================
MDN_URLS = [
    "https://developer.mozilla.org/en-US/docs/Web/HTML",
    "https://developer.mozilla.org/en-US/docs/Web/CSS", 
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript"
]

# ============================================================================
# COMBINED SETS FOR DIFFERENT TEST SCENARIOS
# ============================================================================

# Small test set (1 URL per domain)
SMALL_TEST_SET = [
    GITHUB_URLS[0],      # github.com/features
    STACKOVERFLOW_URLS[0], # stackoverflow.com/questions
    MDN_URLS[0]          # developer.mozilla.org/.../HTML
]

# Medium test set (2 URLs per domain)  
MEDIUM_TEST_SET = [
    GITHUB_URLS[0],      # github.com/features
    GITHUB_URLS[1],      # github.com/pricing
    STACKOVERFLOW_URLS[0], # stackoverflow.com/questions
    STACKOVERFLOW_URLS[1], # stackoverflow.com/tags
    MDN_URLS[0],         # developer.mozilla.org/.../HTML
    MDN_URLS[1]          # developer.mozilla.org/.../CSS
]

# Large test set (all URLs)
LARGE_TEST_SET = GITHUB_URLS + STACKOVERFLOW_URLS + MDN_URLS

# ============================================================================
# CACHE TESTING SCENARIOS
# ============================================================================

def get_cache_test_scenarios():
    """
    Get different URL combinations for testing cache efficiency.
    Each scenario tests different cache hit patterns.
    """
    return {
        "scenario_1_single_domain": {
            "description": "Single domain - tests individual URL caching within same domain",
            "urls": GITHUB_URLS,
            "expected_behavior": "First run: no cache. Subsequent runs: individual URL cache hits"
        },
        
        "scenario_2_mixed_domains": {
            "description": "Mixed domains - tests cross-domain individual caching", 
            "urls": SMALL_TEST_SET,
            "expected_behavior": "Tests individual URL cache across different domains"
        },
        
        "scenario_3_partial_overlap": {
            "description": "Partial overlap - tests partial cache hits",
            "urls": [
                GITHUB_URLS[0],        # Will be cached from scenario_1
                STACKOVERFLOW_URLS[1], # New URL  
                MDN_URLS[2]           # New URL
            ],
            "expected_behavior": "1/3 URLs from cache (33% efficiency)"
        },
        
        "scenario_4_complete_reuse": {
            "description": "Complete reuse - tests 100% cache hit",
            "urls": SMALL_TEST_SET,  # Same as scenario_2
            "expected_behavior": "100% cache hit if run after scenario_2"
        },
        
        "scenario_5_incremental_growth": {
            "description": "Incremental growth - tests cache building",
            "urls": [
                GITHUB_URLS[0],           # From cache
                GITHUB_URLS[1],           # From cache  
                STACKOVERFLOW_URLS[0],     # From cache
                MDN_URLS[1],              # New URL
                MDN_URLS[2]               # New URL
            ],
            "expected_behavior": "3/5 URLs from cache (60% efficiency)"
        }
    }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_test_urls():
    """Print all available test URLs organized by domain."""
    print("🌐 AVAILABLE TEST URLS FOR CACHE OPTIMIZATION")
    print("=" * 60)
    
    print("\n📁 DOMAIN 1: GitHub (github.com)")
    for i, url in enumerate(GITHUB_URLS, 1):
        print(f"   {i}. {url}")
    
    print("\n📁 DOMAIN 2: Stack Overflow (stackoverflow.com)")  
    for i, url in enumerate(STACKOVERFLOW_URLS, 1):
        print(f"   {i}. {url}")
        
    print("\n📁 DOMAIN 3: Mozilla MDN (developer.mozilla.org)")
    for i, url in enumerate(MDN_URLS, 1):
        print(f"   {i}. {url}")
    
    print("\n🎯 READY-TO-USE TEST SETS")
    print("=" * 60)
    print(f"📝 Small set (3 URLs):  {len(SMALL_TEST_SET)} URLs")
    print(f"📝 Medium set (6 URLs): {len(MEDIUM_TEST_SET)} URLs") 
    print(f"📝 Large set (9 URLs):  {len(LARGE_TEST_SET)} URLs")

def print_cache_scenarios():
    """Print cache testing scenarios."""
    print("\n🧪 CACHE TESTING SCENARIOS")
    print("=" * 60)
    
    scenarios = get_cache_test_scenarios()
    for i, (scenario_name, scenario_data) in enumerate(scenarios.items(), 1):
        print(f"\n{i}. {scenario_data['description']}")
        print(f"   URLs ({len(scenario_data['urls'])}): {scenario_data['urls']}")
        print(f"   Expected: {scenario_data['expected_behavior']}")

def get_progressive_test_sequence():
    """
    Get a sequence of URL sets that progressively test cache efficiency.
    Run these in order to see cache building up.
    """
    return [
        {
            "step": 1,
            "name": "Initial Cache Building",
            "urls": [GITHUB_URLS[0], STACKOVERFLOW_URLS[0]],
            "expected_cache": "0% (no cache)",
            "description": "Build initial cache with 2 URLs from different domains"
        },
        {
            "step": 2, 
            "name": "Partial Cache Hit",
            "urls": [GITHUB_URLS[0], MDN_URLS[0]],  # 1 cached, 1 new
            "expected_cache": "50% (1/2 URLs cached)",
            "description": "Reuse 1 URL, add 1 new URL"
        },
        {
            "step": 3,
            "name": "Growing Cache",
            "urls": [GITHUB_URLS[0], STACKOVERFLOW_URLS[0], MDN_URLS[0]], # All cached individually
            "expected_cache": "100% (all individual URLs cached)",
            "description": "All URLs should be in individual cache"
        },
        {
            "step": 4,
            "name": "Mixed Expansion", 
            "urls": [GITHUB_URLS[1], STACKOVERFLOW_URLS[0], MDN_URLS[1]], # 1 cached, 2 new
            "expected_cache": "33% (1/3 URLs cached)",
            "description": "Add new URLs while reusing some cached ones"
        },
        {
            "step": 5,
            "name": "Complete Cache Hit",
            "urls": [GITHUB_URLS[0], STACKOVERFLOW_URLS[0], MDN_URLS[0]], # Same as step 3
            "expected_cache": "100% (complete cache hit)",
            "description": "Should hit complete cache from step 3"
        }
    ]

# ============================================================================
# QUICK ACCESS VARIABLES (for copy-paste into UI)
# ============================================================================

# Quick URLs for copy-paste into your UI
QUICK_TEST_URLS_TEXT = """https://github.com/features
https://github.com/pricing
https://stackoverflow.com/questions
https://stackoverflow.com/tags
https://developer.mozilla.org/en-US/docs/Web/HTML
https://developer.mozilla.org/en-US/docs/Web/CSS"""

# Single domain test
GITHUB_ONLY_TEXT = """https://github.com/features
https://github.com/pricing
https://github.com/enterprise"""

# Cross-domain test
CROSS_DOMAIN_TEXT = """https://github.com/features
https://stackoverflow.com/questions
https://developer.mozilla.org/en-US/docs/Web/HTML"""

if __name__ == "__main__":
    print_test_urls()
    print_cache_scenarios()
    
    print("\n🚀 PROGRESSIVE TESTING SEQUENCE")
    print("=" * 60)
    print("Run these in order to see cache optimization in action:")
    
    sequence = get_progressive_test_sequence()
    for step in sequence:
        print(f"\n📋 Step {step['step']}: {step['name']}")
        print(f"   URLs: {step['urls']}")
        print(f"   Expected: {step['expected_cache']}")
        print(f"   Purpose: {step['description']}")
    
    print(f"\n📝 QUICK COPY-PASTE URLs:")
    print("=" * 60)
    print("🎯 Cross-Domain Test (3 URLs):")
    print(CROSS_DOMAIN_TEXT)
    print("\n🎯 GitHub Only Test (3 URLs):")  
    print(GITHUB_ONLY_TEXT)
    print("\n🎯 Mixed Test (6 URLs):")
    print(QUICK_TEST_URLS_TEXT) 