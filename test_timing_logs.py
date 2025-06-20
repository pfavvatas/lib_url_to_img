#!/usr/bin/env python3
"""
Test script to verify comprehensive timing logs functionality
"""

import requests
import json
import time
import os

def format_duration(seconds):
    """Format duration in a readable way"""
    if seconds < 1:
        return f"{(seconds * 1000):.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"

def format_file_size(bytes_size):
    """Format file size in a readable way"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.2f} MB"

def print_section_header(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")

def print_subsection_header(title):
    """Print a subsection header"""
    print(f"\n{'─'*40}")
    print(f"🔍 {title}")
    print(f"{'─'*40}")

def analyze_timing_logs(timing_logs, indent=0):
    """Recursively analyze and display timing logs"""
    if not timing_logs:
        return
    
    indent_str = "  " * indent
    
    # Overall Performance Metrics
    if "performance_metrics" in timing_logs:
        print_section_header("OVERALL PERFORMANCE METRICS")
        metrics = timing_logs["performance_metrics"]
        print(f"⏱️  Total Processing Time: {format_duration(metrics.get('total_processing_time', 0))}")
        print(f"🌐 Average Time per URL: {format_duration(metrics.get('average_time_per_url', 0))}")
        print(f"📊 Average Time per Level: {format_duration(metrics.get('average_time_per_level', 0))}")
        print(f"🔗 URLs Processed: {metrics.get('urls_processed', 0)}")
        print(f"📈 Levels Processed: {metrics.get('levels_processed', 0)}")
        print(f"📄 HTML Files Generated: {metrics.get('html_files_generated', 0)}")
        print(f"🎯 Clusters Generated: {metrics.get('clusters_generated', 0)}")
    
    # Step-by-Step Timing
    if "steps" in timing_logs:
        print_section_header("STEP-BY-STEP TIMING ANALYSIS")
        steps = timing_logs["steps"]
        
        for step_name, step_data in steps.items():
            print_subsection_header(f"{step_data.get('description', step_name)}")
            print(f"⏱️  Duration: {format_duration(step_data.get('duration', 0))}")
            print(f"🕐 Start: {time.strftime('%H:%M:%S', time.localtime(step_data.get('start_time', 0)))}")
            print(f"🕐 End: {time.strftime('%H:%M:%S', time.localtime(step_data.get('end_time', 0)))}")
            
            # Step-specific details
            if step_name == "data_collection":
                print(f"📊 URLs Processed: {step_data.get('urls_processed', 0)}")
                print(f"📈 Levels Processed: {step_data.get('levels_processed', [])}")
                
                # URL-specific timing
                if "url_timing_logs" in step_data:
                    print(f"\n📋 Per-URL Detailed Timing:")
                    for url_id, url_timing in step_data["url_timing_logs"].items():
                        print(f"  🔗 {url_timing.get('url', 'Unknown URL')}")
                        print(f"    ⏱️  Total: {format_duration(url_timing.get('total_duration', 0))}")
                        
                        # File operations for this URL
                        if "file_operations" in url_timing:
                            print(f"    📁 Files Created:")
                            for file_op_name, file_op_data in url_timing["file_operations"].items():
                                print(f"      📄 {file_op_data.get('file_name', 'Unknown')}: {format_duration(file_op_data.get('duration', 0))}")
                        
                        # Steps for this URL
                        if "steps" in url_timing:
                            print(f"    🔄 Steps:")
                            for step_key, step_info in url_timing["steps"].items():
                                print(f"      ⚡ {step_info.get('description', step_key)}: {format_duration(step_info.get('duration', 0))}")
            
            elif step_name == "data_saving":
                print(f"💾 File: {step_data.get('file_name', 'Unknown')}")
                print(f"📏 File Size: {format_file_size(step_data.get('file_size_bytes', 0))}")
                print(f"🔢 URLs Saved: {step_data.get('urls_saved', 0)}")
                print(f"🆔 Total Unique IDs: {step_data.get('total_unique_ids', 0)}")
            
            elif step_name == "computed_styles_generation":
                print(f"📊 Total Unique Attributes: {step_data.get('total_unique_attributes', 0)}")
                print(f"📈 Levels Processed: {step_data.get('levels_processed', [])}")
            
            elif step_name.startswith("clustering_level_"):
                level = step_data.get('level', 'Unknown')
                print(f"📊 Level: {level}")
                print(f"📄 Computed Styles File: {os.path.basename(step_data.get('computed_styles_file', 'Unknown'))}")
                print(f"📏 File Size: {format_file_size(step_data.get('file_size_bytes', 0))}")
                print(f"🎯 Clusters Generated: {step_data.get('clusters_generated', 0)}")
                print(f"📊 DBCV Score: {step_data.get('dbcv_score', 0):.3f}")
                print(f"🔧 Useful Attributes: {step_data.get('useful_attributes_count', 0)}")
                
                # Sub-steps
                if "sub_steps" in step_data:
                    print(f"  📋 Sub-steps:")
                    for sub_step_name, sub_step_data in step_data["sub_steps"].items():
                        print(f"    ⚡ {sub_step_data.get('description', sub_step_name)}: {format_duration(sub_step_data.get('duration', 0))}")
                        if "file_size_bytes" in sub_step_data:
                            print(f"      📏 File Size: {format_file_size(sub_step_data.get('file_size_bytes', 0))}")
                        if "html_files_created" in sub_step_data:
                            print(f"      📄 HTML Files: {sub_step_data.get('html_files_created', 0)}")
                        if "algorithm" in sub_step_data:
                            print(f"      🤖 Algorithm: {sub_step_data.get('algorithm', 'Unknown')}")
            
            elif step_name == "html_generation":
                print(f"📄 HTML Files Created: {step_data.get('html_files_created', 0)}")
                print(f"📏 Total HTML Size: {format_file_size(step_data.get('total_html_size_bytes', 0))}")
                print(f"📊 Average File Size: {format_file_size(step_data.get('average_file_size_bytes', 0))}")
                print(f"⚡ Files per Second: {step_data.get('files_per_second', 0):.2f}")
                print(f"🚀 Bytes per Second: {format_file_size(step_data.get('bytes_per_second', 0))}/s")
            
            elif step_name == "results_writing":
                print(f"📄 File: {os.path.basename(step_data.get('file_path', 'Unknown'))}")
                print(f"📏 File Size: {format_file_size(step_data.get('file_size_after_bytes', 0))}")
                print(f"📈 Size Change: {format_file_size(step_data.get('file_size_change_bytes', 0))}")
                print(f"⚡ Write Speed: {step_data.get('write_speed_mb_per_second', 0):.2f} MB/s")
            
            elif step_name == "guid_processing":
                print(f"🆔 Total GUIDs: {step_data.get('total_guids', 0)}")
                print(f"🌐 Sites Found: {step_data.get('sites_found', 0)}")
                print(f"📏 File Size: {format_file_size(step_data.get('file_size_bytes', 0))}")
                print(f"🔢 GUID Count: {step_data.get('guid_count', 0)}")
                print(f"⚡ Processed GUIDs: {step_data.get('processed_guids', 0)}")
                
                # File operations
                if "file_operations" in step_data:
                    print(f"  📁 File Operations:")
                    for op_name, op_data in step_data["file_operations"].items():
                        print(f"    📄 {op_name}: {format_duration(op_data.get('duration', 0))}")
                        if "file_size_bytes" in op_data:
                            print(f"      📏 Size: {format_file_size(op_data.get('file_size_bytes', 0))}")
                        if "processing_rate" in op_data:
                            print(f"      ⚡ Rate: {op_data.get('processing_rate', 0):.2f} GUIDs/s")
    
    # Cluster Information
    if "cluster_info" in timing_logs:
        print_section_header("CLUSTER INFORMATION")
        cluster_info = timing_logs["cluster_info"]
        
        for level_key, cluster_data in cluster_info.items():
            print_subsection_header(f"Level {cluster_data.get('level', level_key.replace('level_', ''))}")
            print(f"🎯 Number of Clusters: {cluster_data.get('num_clusters', 0)}")
            print(f"📊 DBCV Score: {cluster_data.get('dbcv_score', 0):.3f}")
            print(f"📏 Min Cluster Size: {cluster_data.get('min_cluster_size', 0)}")
            print(f"⚙️  Epsilon: {cluster_data.get('cluster_selection_epsilon', 0)}")
            
            if "useful_attributes" in cluster_data:
                print(f"🔧 Useful Attributes ({len(cluster_data['useful_attributes'])}):")
                for attr in cluster_data["useful_attributes"]:
                    print(f"  • {attr}")

def test_timing_logs():
    """Test the comprehensive timing logs functionality"""
    
    # Test data
    test_data = {
        "urls": ["https://www.example.com"],
        "levels": [1],
        "mode": 0
    }
    
    print("🚀 Testing Comprehensive Timing Logs Functionality...")
    print("=" * 80)
    
    try:
        # Make the API call
        start_time = time.time()
        response = requests.post(
            "http://localhost:5000/process-urls",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        api_call_time = time.time() - start_time
        
        print(f"🌐 API call completed in {format_duration(api_call_time)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response status: {data.get('status')}")
            print(f"📝 Response message: {data.get('message')}")
            
            # Check if timing logs are present
            timing_logs = data.get('timing_logs')
            if timing_logs:
                print("\n🎉 Comprehensive timing logs found!")
                
                # Analyze and display timing logs
                analyze_timing_logs(timing_logs)
                
                # Save detailed timing logs to file for inspection
                with open('comprehensive_timing_logs.json', 'w') as f:
                    json.dump(timing_logs, f, indent=2)
                print(f"\n💾 Detailed timing logs saved to: comprehensive_timing_logs.json")
                
                # Generate summary report
                print_section_header("SUMMARY REPORT")
                performance_metrics = timing_logs.get('performance_metrics', {})
                print(f"📊 Total Processing Time: {format_duration(performance_metrics.get('total_processing_time', 0))}")
                print(f"🌐 URLs Processed: {performance_metrics.get('urls_processed', 0)}")
                print(f"📈 Levels Processed: {performance_metrics.get('levels_processed', 0)}")
                print(f"📄 HTML Files Generated: {performance_metrics.get('html_files_generated', 0)}")
                print(f"🎯 Clusters Generated: {performance_metrics.get('clusters_generated', 0)}")
                
                # Calculate efficiency metrics
                total_time = performance_metrics.get('total_processing_time', 0)
                urls_processed = performance_metrics.get('urls_processed', 1)
                html_files = performance_metrics.get('html_files_generated', 0)
                clusters = performance_metrics.get('clusters_generated', 0)
                
                print(f"\n⚡ Efficiency Metrics:")
                print(f"  🚀 URLs per second: {urls_processed / total_time:.2f}" if total_time > 0 else "  🚀 URLs per second: N/A")
                print(f"  📄 HTML files per second: {html_files / total_time:.2f}" if total_time > 0 else "  📄 HTML files per second: N/A")
                print(f"  🎯 Clusters per second: {clusters / total_time:.2f}" if total_time > 0 else "  🎯 Clusters per second: N/A")
                
            else:
                print("❌ No timing logs found in response")
                
        else:
            print(f"❌ API call failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timing_logs() 