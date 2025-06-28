import json
import os
import itertools
import random
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
import shutil
import sys

# Add the lib directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from lib import process_urls_from_api

class ExperimentManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to the config file in the same directory as this module
            config_path = os.path.join(os.path.dirname(__file__), "test_scenarios_config.json")
        self.config_path = config_path
        self.config = self.load_config()
        self.base_results_dir = "experiment_results"
        self.current_experiment_dir = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load the test scenarios configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file {self.config_path} not found")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in configuration file: {e}")
    
    def generate_test_combinations(self) -> List[Dict[str, Any]]:
        """Generate all possible test combinations based on configuration"""
        test_cases = []
        config = self.config['test_configuration']
        params = config['test_parameters']
        rules = self.config['test_generation_rules']
        
        available_urls = config['available_urls']
        modes = params['modes']
        level_combinations = []
        
        # Collect all level combinations
        for combo_type, levels in params['level_combinations'].items():
            level_combinations.extend(levels)
        
        # Generate URL set sizes
        url_sizes = []
        for size_type, sizes in config['url_combinations'].items():
            url_sizes.extend(sizes)
        
        test_index = 1
        
        # Remove the artificial limit - generate all valid combinations
        # max_per_mode = rules['filters']['max_combinations_per_run'] // len(modes)
        # max_total_combinations = rules['filters']['max_combinations_per_run']  # DISABLED: No test limits
        max_total_combinations = float('inf')  # No limit on test combinations
        
        for mode in modes:
            for levels in level_combinations:
                for url_count in url_sizes:
                    if url_count <= len(available_urls):
                        # For each parameter set, create multiple URL combinations
                        # Calculate how many different URL combinations we can make
                        import itertools
                        import math
                        
                        # Calculate number of possible combinations
                        total_possible = math.comb(len(available_urls), url_count) if url_count <= len(available_urls) else 0
                        
                        # Limit variations to reasonable number (max 5 per parameter set)
                        variations_limit = min(5, total_possible, max_total_combinations - len(test_cases))
                        
                        # Generate different URL combinations
                        if variations_limit > 0:
                            import random
                            used_combinations = set()
                            
                            for variation in range(variations_limit):
                                # Skip if we've reached the total limit
                                if len(test_cases) >= max_total_combinations:
                                    break
                                
                                # Generate unique URL combinations
                                max_attempts = 50  # Prevent infinite loops
                                attempts = 0
                                while attempts < max_attempts:
                                    selected_urls = sorted(random.sample(available_urls, url_count))
                                    url_tuple = tuple(selected_urls)
                                    
                                    # Ensure this combination hasn't been used for this mode/level combination
                                    combo_key = (mode, tuple(levels if isinstance(levels, list) else [levels]), url_tuple)
                                    if combo_key not in used_combinations:
                                        used_combinations.add(combo_key)
                                        break
                                    attempts += 1
                                
                                if attempts >= max_attempts:
                                    # If we can't find unique combinations, use what we have
                                    selected_urls = sorted(random.sample(available_urls, url_count))
                                
                                # Create test case
                                levels_list = levels if isinstance(levels, list) else [levels]
                                test_case = {
                                    "id": f"test_{test_index:03d}_{mode}_L{'_'.join(map(str, levels_list))}_U{url_count}_V{variation + 1}",
                                    "name": f"Mode {mode} - Levels {levels_list} - {url_count} URLs (Var {variation + 1})",
                                    "description": f"Testing Mode {mode} with levels {levels_list} using {url_count} URLs (variation {variation + 1})",
                                    "mode": mode,
                                    "levels": levels_list,
                                    "urls": selected_urls,
                                    "url_count": url_count,
                                    "variation": variation + 1,
                                    "estimated_duration": self.estimate_test_duration(url_count, levels_list),
                                    "priority": self.calculate_priority(mode, levels_list, url_count)
                                }
                                test_cases.append(test_case)
                                test_index += 1
                                
                                # Break if we've reached the total limit
                                if len(test_cases) >= max_total_combinations:
                                    break
                        
                        # Break if we've reached the total limit
                        if len(test_cases) >= max_total_combinations:
                            break
                    
                # Break if we've reached the total limit
                if len(test_cases) >= max_total_combinations:
                    break
            
            # Break if we've reached the total limit
            if len(test_cases) >= max_total_combinations:
                break
        
        print(f"Generated {len(test_cases)} test combinations")
        return test_cases
    
    def estimate_test_duration(self, url_count: int, levels) -> float:
        """Estimate test duration in minutes"""
        base_time_per_url = 0.5  # minutes
        level_multiplier = len(levels) if isinstance(levels, list) else 1
        return url_count * base_time_per_url * level_multiplier
    
    def calculate_priority(self, mode: int, levels, url_count: int) -> str:
        """Calculate test priority based on parameters"""
        level_count = len(levels) if isinstance(levels, list) else 1
        
        if level_count <= 2 and url_count <= 5:
            return "high"
        elif level_count <= 3 and url_count <= 7:
            return "medium"
        else:
            return "low"
    
    def create_experiment_directory(self, experiment_name: str = None) -> str:
        """Create a timestamped experiment directory"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if experiment_name:
            dir_name = f"{timestamp}_{experiment_name}"
        else:
            dir_name = f"{timestamp}_experiment"
        
        self.current_experiment_dir = os.path.join(self.base_results_dir, dir_name)
        os.makedirs(self.current_experiment_dir, exist_ok=True)
        
        # Create subdirectories
        os.makedirs(os.path.join(self.current_experiment_dir, "test_cases"), exist_ok=True)
        os.makedirs(os.path.join(self.current_experiment_dir, "summary"), exist_ok=True)
        os.makedirs(os.path.join(self.current_experiment_dir, "gnuplot_data"), exist_ok=True)
        
        return self.current_experiment_dir
    
    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case"""
        print(f"🧪 Running test: {test_case['id']}")
        
        start_time = time.time()
        
        try:
            # Run the URL processing with the flat URL array
            result = process_urls_from_api(
                urls=test_case['urls'],
                levels=test_case['levels'],
                mode=test_case['mode']
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Add test metadata to result (preserve existing timing logs)
            result['test_metadata'] = {
                'test_id': test_case['id'],
                'test_name': test_case['name'],
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'mode': test_case['mode'],
                'levels': test_case['levels'],
                'url_count': test_case['url_count'],
                'urls': test_case['urls']
            }
            
            # Preserve detailed timing logs from the processing
            if 'timing_logs' not in result:
                result['timing_logs'] = {}
            
            # Add experiment-level timing to the existing timing logs
            if 'experiment_timing' not in result['timing_logs']:
                result['timing_logs']['experiment_timing'] = {
                    'test_start_time': start_time,
                    'test_end_time': end_time,
                    'test_duration': duration,
                    'test_id': test_case['id']
                }
            
            # Save individual test result
            if self.current_experiment_dir:
                test_dir = os.path.join(self.current_experiment_dir, "test_cases", test_case['id'])
                os.makedirs(test_dir, exist_ok=True)
                
                with open(os.path.join(test_dir, "results.json"), 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                
                with open(os.path.join(test_dir, "test_config.json"), 'w') as f:
                    json.dump(test_case, f, indent=2)
            
            print(f"✅ Test {test_case['id']} completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            error_result = {
                'status': 'error',
                'message': str(e),
                'test_metadata': {
                    'test_id': test_case['id'],
                    'test_name': test_case['name'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'mode': test_case['mode'],
                    'levels': test_case['levels'],
                    'url_count': test_case['url_count'],
                    'urls': test_case['urls']
                }
            }
            
            print(f"❌ Test {test_case['id']} failed: {str(e)}")
            return error_result
    
    def run_experiment_batch(self, test_cases: List[Dict[str, Any]], experiment_name: str = None) -> Dict[str, Any]:
        """Run a batch of test cases"""
        experiment_dir = self.create_experiment_directory(experiment_name)
        
        print(f"🚀 Starting experiment batch with {len(test_cases)} test cases")
        print(f"📁 Results will be saved to: {experiment_dir}")
        
        experiment_start_time = time.time()
        results = []
        successful_tests = 0
        failed_tests = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 Progress: {i}/{len(test_cases)} tests")
            
            result = self.run_single_test(test_case)
            results.append(result)
            
            if result.get('status') == 'success':
                successful_tests += 1
            else:
                failed_tests += 1
        
        experiment_end_time = time.time()
        experiment_duration = experiment_end_time - experiment_start_time
        
        # REVERTED: Keep original data without separating to large files
        # User prefers direct access to clustering data without additional API calls
        print(f"\n📊 Keeping all clustering data directly in results - no separation to large files")
        
        # Calculate original data size for information
        original_size = len(json.dumps(results, default=str).encode('utf-8'))
        print(f"📊 Total experiment data size: {original_size / 1024:.1f} KB")
        
        # Create experiment summary with FULL original results
        summary = {
            'experiment_info': {
                'name': experiment_name or 'Unnamed Experiment',
                'start_time': experiment_start_time,
                'end_time': experiment_end_time,
                'duration': experiment_duration,
                'total_tests': len(test_cases),
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': (successful_tests / len(test_cases)) * 100,
                'data_optimization': {
                    'large_data_separated': False,
                    'original_size_kb': original_size / 1024,
                    'optimized_size_kb': original_size / 1024,
                    'size_reduction_percent': 0,
                    'note': 'Data optimization disabled - clustering data included directly'
                }
            },
            'test_cases': test_cases,
            'results': results  # Use FULL original results with all clustering data
        }
        
        # Save experiment summary with optimized data
        with open(os.path.join(experiment_dir, "experiment_summary.json"), 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Generate gnuplot data and execute scripts
        generated_images, execution_log = self.generate_gnuplot_data(results, experiment_dir)
        
        # Add gnuplot information to summary
        summary['gnuplot_info'] = {
            'generated_images': generated_images,
            'execution_log': execution_log,
            'total_images': len(generated_images)
        }
        
        # Update experiment summary file with gnuplot info
        with open(os.path.join(experiment_dir, "experiment_summary.json"), 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n🎉 Experiment completed!")
        print(f"✅ Successful tests: {successful_tests}")
        print(f"❌ Failed tests: {failed_tests}")
        print(f"⏱️ Total duration: {experiment_duration:.2f}s")
        print(f"📊 Generated {len(generated_images)} gnuplot images")
        
        return summary
    
    def generate_gnuplot_data(self, results: List[Dict[str, Any]], experiment_dir: str):
        """
        Generate comprehensive data files for gnuplot charts with detailed metrics
        
        GNUPLOT DATA GENERATION CONFIGURATION:
        To enable/disable specific data files and plots, comment/uncomment the corresponding 
        sections below marked with "CONFIGURABLE SECTION"
        """
        gnuplot_dir = os.path.join(experiment_dir, "gnuplot_data")
        
        # ==============================================
        # GNUPLOT DATA GENERATION CONFIGURATION
        # ==============================================
        # Enable/disable data file generation by commenting/uncommenting these flags
        # Set to True to generate, False to skip
        
        # Basic Data Files Configuration
        GENERATE_BASIC_DATA = {
            'processing_times': True,       # Processing time by test case
            'cluster_counts': True,         # Number of clusters per level
            'html_file_counts': True,       # HTML files generated per test
            'timing_analysis': True,        # Detailed timing metrics
            'cache_efficiency': True,       # Cache hit/miss statistics
            'step_timing': True,           # Step-by-step timing breakdown
        }
        
        # Enhanced Metrics Configuration
        GENERATE_ENHANCED_DATA = {
            'url_processing_times': True,           # Per-URL processing times
            'clustering_times_by_level': True,     # Detailed clustering timing by level
            'similarity_analysis_times': True,     # Site similarity analysis timing
            'level_performance_breakdown': True,   # Performance breakdown by DOM level
            'mode_comparison_metrics': True,       # Mode 0 vs Mode 1 comparison
            'comprehensive_experiment_metrics': True,  # Overall experiment statistics
        }
        
        # Gnuplot Scripts Configuration
        GENERATE_SCRIPTS = {
            'processing_time_plots': True,      # Processing time comparison charts
            'cluster_count_plots': True,        # Clustering results charts
            'cache_efficiency_plots': True,     # Cache performance charts
            'timing_analysis_plots': True,      # Detailed timing analysis charts
            'performance_dashboard': True,      # Multi-chart dashboard
            'domain_specific_plots': True,      # Domain-specific analysis for Mode 1
        }
        
        # Output Formats Configuration (comment out unwanted formats)
        OUTPUT_FORMATS = [
            ("png", "png size 1200,800 font 'Arial,12'"),
            # ("ps", "postscript enhanced color solid font 'Arial,12'"),
            # ("eps", "postscript eps enhanced color solid font 'Arial,12'"),
            # ("svg", "svg size 1200,800 font 'Arial,12'"),    # Uncomment for SVG
            # ("tex", "epslatex color solid")                  # Uncomment for LaTeX
        ]
        
        # Auto-execution Configuration
        AUTO_EXECUTE_GNUPLOT = True  # Set to False to only generate scripts without executing
        
        # ===============================================================
        # 📚 CONFIGURATION GUIDE - HOW TO CUSTOMIZE GNUPLOT GENERATION
        # ===============================================================
        """
        USAGE EXAMPLES:
        
        1. TO GENERATE ONLY PROCESSING TIME DATA AND PLOTS:
           GENERATE_BASIC_DATA = {'processing_times': True, 'cluster_counts': False, ...}
           GENERATE_SCRIPTS = {'processing_time_plots': True, 'cluster_count_plots': False, ...}
        
        2. TO DISABLE ALL ENHANCED METRICS:
           GENERATE_ENHANCED_DATA = {key: False for key in GENERATE_ENHANCED_DATA}
        
        3. TO GENERATE ONLY PNG FORMAT:
           OUTPUT_FORMATS = [("png", "png size 1200,800 font 'Arial,12'")]
        
        4. TO GENERATE SCRIPTS WITHOUT EXECUTING:
           AUTO_EXECUTE_GNUPLOT = False
        
        5. TO DISABLE SPECIFIC PLOTS:
           # Comment out the unwanted plot types:
           GENERATE_SCRIPTS = {
               'processing_time_plots': True,      # Keep this
               # 'cluster_count_plots': False,     # Commented out = disabled
               'cache_efficiency_plots': True,     # Keep this
               # 'timing_analysis_plots': False,   # Commented out = disabled
               'performance_dashboard': True,      # Keep this
           }
           
        AVAILABLE DATA FILES:
        - processing_times.dat: Test execution times by mode/URL count
        - cluster_counts.dat: Number of clusters generated per DOM level
        - html_file_counts.dat: HTML files created per test
        - timing_analysis.dat: Detailed performance breakdowns
        - cache_efficiency.dat: Cache hit/miss statistics
        - step_timing.dat: Step-by-step execution timing
        - url_processing_times.dat: Per-URL processing details
        - clustering_times_by_level.dat: Clustering performance by level
        - similarity_analysis_times.dat: Site similarity computation times
        - level_performance_breakdown.dat: Performance analysis by DOM level
        - mode_comparison_metrics.dat: Mode 0 vs Mode 1 comparisons
        - comprehensive_experiment_metrics.dat: Overall experiment statistics
        
        AVAILABLE PLOT TYPES:
        - processing_time_plots: Processing time comparison charts (Mode 0 vs Mode 1)
        - cluster_count_plots: Clustering results visualization
        - cache_efficiency_plots: Cache performance analysis
        - timing_analysis_plots: Detailed timing breakdowns
        - performance_dashboard: Multi-chart dashboard view
        """
        
        print(f"\n📊 GNUPLOT CONFIGURATION:")
        print(f"   📁 Basic data files: {sum(GENERATE_BASIC_DATA.values())}/{len(GENERATE_BASIC_DATA)} enabled")
        print(f"   📈 Enhanced metrics: {sum(GENERATE_ENHANCED_DATA.values())}/{len(GENERATE_ENHANCED_DATA)} enabled")
        print(f"   🎨 Script types: {sum(GENERATE_SCRIPTS.values())}/{len(GENERATE_SCRIPTS)} enabled")
        print(f"   🖼️  Output formats: {len(OUTPUT_FORMATS)} formats")
        print(f"   ⚡ Auto-execute: {'Yes' if AUTO_EXECUTE_GNUPLOT else 'No'}")
        print(f"\n📊 EXTRACTING COMPREHENSIVE METRICS from {len(results)} results...")
        
        # Enhanced data collection for comprehensive analysis
        processing_times = []
        cluster_counts = []
        similarity_scores = []
        html_file_counts = []
        timing_analysis = []
        cache_efficiency = []
        step_timing = []
        
        # NEW: Detailed metrics by levels, modes, URLs
        url_processing_times = []
        clustering_times_by_level = []
        similarity_analysis_times = []
        level_performance_breakdown = []
        mode_comparison_metrics = []
        comprehensive_experiment_metrics = []
        
        print(f"\n📊 EXTRACTING COMPREHENSIVE METRICS from {len(results)} results...")
        
        for result in results:
            if result.get('status') == 'success':
                metadata = result.get('test_metadata', {})
                timing_logs = result.get('timing_logs', {})
                
                test_id = metadata.get('test_id', '')
                mode = metadata.get('mode', 0)
                levels = metadata.get('levels', [])
                url_count = metadata.get('url_count', 0)
                urls = metadata.get('urls', [])
                
                # NEW: Process Mode 1 domain-specific timing data
                if mode == 1 and 'domain_results' in result:
                    for domain_result in result['domain_results']:
                        domain_timing = domain_result.get('timing_logs', {})
                        domain_name = domain_result.get('domain', 'unknown')
                        
                        # Process domain-specific timing for each step
                        if domain_timing.get('steps'):
                            for step_name, step_data in domain_timing['steps'].items():
                                if step_name.startswith('clustering_level_'):
                                    level = step_data.get('level', 0)
                                    sub_steps = step_data.get('sub_steps', {})
                                    
                                    # Add domain-specific clustering times
                                    clustering_times_by_level.append({
                                        'test_id': f"{test_id}_{domain_name}",
                                        'mode': mode,
                                        'domain': domain_name,
                                        'level': level,
                                        'url_count': len(domain_result.get('urls', [])),
                                        'total_clustering_time': step_data.get('duration', 0),
                                        'file_reading_time': sub_steps.get('file_reading', {}).get('duration', 0),
                                        'clustering_analysis_time': sub_steps.get('clustering_analysis', {}).get('duration', 0),
                                        'cluster_processing_time': sub_steps.get('cluster_processing', {}).get('duration', 0),
                                        'file_size_mb': step_data.get('file_size_mb', 0),
                                        'clusters_generated': step_data.get('clusters_generated', 0),
                                        'dbcv_score': step_data.get('dbcv_score', 0),
                                        'useful_attributes_count': step_data.get('useful_attributes_count', 0)
                                    })
                        
                        # Add domain-specific processing times
                        if domain_timing.get('performance_metrics'):
                            domain_perf = domain_timing['performance_metrics']
                            processing_times.append({
                                'test_id': f"{test_id}_{domain_name}",
                                'mode': mode,
                                'domain': domain_name,
                                'levels_str': '_'.join(map(str, levels)),
                                'url_count': len(domain_result.get('urls', [])),
                                'duration': domain_perf.get('total_processing_time', 0)
                            })
                        
                        # Add domain-specific comprehensive metrics
                        if domain_timing.get('performance_metrics'):
                            domain_perf = domain_timing['performance_metrics']
                            comprehensive_experiment_metrics.append({
                                'test_id': f"{test_id}_{domain_name}",
                                'mode': mode,
                                'domain': domain_name,
                                'url_count': len(domain_result.get('urls', [])),
                                'levels_count': len(levels),
                                'total_time': domain_perf.get('total_processing_time', 0),
                                'cache_efficiency': domain_perf.get('cache_efficiency_percent', 0),
                                'urls_from_cache': domain_perf.get('urls_from_cache', 0),
                                'urls_newly_processed': domain_perf.get('urls_newly_processed', 0),
                                'html_files_generated': domain_perf.get('html_files_generated', 0),
                                'clusters_generated': domain_perf.get('clusters_generated', 0),
                                'avg_time_per_url': domain_perf.get('average_time_per_url', 0),
                                'avg_time_per_level': domain_perf.get('average_time_per_level', 0),
                                'processing_efficiency': (domain_perf.get('html_files_generated', 0) / domain_perf.get('total_processing_time', 1)) if domain_perf.get('total_processing_time', 0) > 0 else 0
                            })
                
                # Basic processing time data
                processing_times.append({
                    'test_id': test_id,
                    'mode': mode,
                    'levels_str': '_'.join(map(str, levels)),
                    'url_count': url_count,
                    'duration': metadata.get('duration', 0)
                })
                
                # NEW: URL-level processing times
                if timing_logs.get('performance_metrics'):
                    perf = timing_logs['performance_metrics']
                    for i, url in enumerate(urls):
                        url_processing_times.append({
                            'test_id': test_id,
                            'mode': mode,
                            'url_index': i + 1,
                            'url': url,
                            'url_count': url_count,
                            'total_test_time': perf.get('total_processing_time', 0),
                            'avg_time_per_url': perf.get('average_time_per_url', 0),
                            'estimated_url_time': perf.get('average_time_per_url', 0),
                            'cache_efficiency': perf.get('cache_efficiency_percent', 0),
                            'from_cache': i < perf.get('urls_from_cache', 0)
                        })
                
                # NEW: Clustering times by level with detailed breakdown
                if timing_logs.get('steps'):
                    for step_name, step_data in timing_logs['steps'].items():
                        if step_name.startswith('clustering_level_'):
                            level = step_data.get('level', 0)
                            sub_steps = step_data.get('sub_steps', {})
                            
                            clustering_times_by_level.append({
                                'test_id': test_id,
                                'mode': mode,
                                'level': level,
                                'url_count': url_count,
                                'total_clustering_time': step_data.get('duration', 0),
                                'file_reading_time': sub_steps.get('file_reading', {}).get('duration', 0),
                                'clustering_analysis_time': sub_steps.get('clustering_analysis', {}).get('duration', 0),
                                'cluster_processing_time': sub_steps.get('cluster_processing', {}).get('duration', 0),
                                'file_size_mb': step_data.get('file_size_mb', 0),
                                'clusters_generated': step_data.get('clusters_generated', 0),
                                'dbcv_score': step_data.get('dbcv_score', 0),
                                'useful_attributes_count': step_data.get('useful_attributes_count', 0)
                            })
                
                # NEW: Similarity analysis times (from processed clusters)
                processed_clusters = result.get('processed_clusters', [])
                for proc_cluster in processed_clusters:
                    if proc_cluster.get('timing_summary'):
                        timing_sum = proc_cluster['timing_summary']
                        similarity_analysis_times.append({
                            'test_id': test_id,
                            'mode': mode,
                            'level': proc_cluster.get('level', 0),
                            'url_count': url_count,
                            'similarity_duration': timing_sum.get('site_similarity_duration', 0),
                            'html_files_created': timing_sum.get('html_files_created', 0),
                            'total_cluster_processing': timing_sum.get('total_duration', 0),
                            'sites_count': proc_cluster.get('summary', {}).get('sites_count', 0),
                            'has_similarity_data': proc_cluster.get('summary', {}).get('has_similarity_data', False)
                        })
                
                # NEW: Level performance breakdown
                for level in levels:
                    # Find clustering time for this level
                    clustering_time = 0
                    similarity_time = 0
                    clusters_count = 0
                    dbcv_score = 0
                    
                    # Get clustering metrics
                    for cluster_result in result.get('clustering_results', []):
                        if cluster_result.get('level') == level:
                            if cluster_result.get('cluster_summary'):
                                clusters_count = cluster_result['cluster_summary'].get('num_clusters', 0)
                                dbcv_score = cluster_result['cluster_summary'].get('dbcv_score', 0)
                    
                    # Get timing from step logs
                    if timing_logs.get('steps'):
                        clustering_step = timing_logs['steps'].get(f'clustering_level_{level}', {})
                        clustering_time = clustering_step.get('duration', 0)
                    
                    # Get similarity time from processed clusters
                    for proc_cluster in processed_clusters:
                        if proc_cluster.get('level') == level:
                            similarity_time = proc_cluster.get('timing_summary', {}).get('site_similarity_duration', 0)
                    
                    level_performance_breakdown.append({
                        'test_id': test_id,
                        'mode': mode,
                        'level': level,
                        'url_count': url_count,
                        'clustering_time': clustering_time,
                        'similarity_time': similarity_time,
                        'total_level_time': clustering_time + similarity_time,
                        'clusters_count': clusters_count,
                        'dbcv_score': dbcv_score
                    })
                
                # NEW: Comprehensive experiment metrics
                if timing_logs.get('performance_metrics'):
                    perf = timing_logs['performance_metrics']
                    comprehensive_experiment_metrics.append({
                        'test_id': test_id,
                        'mode': mode,
                        'url_count': url_count,
                        'levels_count': len(levels),
                        'total_time': perf.get('total_processing_time', 0),
                        'cache_efficiency': perf.get('cache_efficiency_percent', 0),
                        'urls_from_cache': perf.get('urls_from_cache', 0),
                        'urls_newly_processed': perf.get('urls_newly_processed', 0),
                        'html_files_generated': perf.get('html_files_generated', 0),
                        'clusters_generated': perf.get('clusters_generated', 0),
                        'avg_time_per_url': perf.get('average_time_per_url', 0),
                        'avg_time_per_level': perf.get('average_time_per_level', 0),
                        'processing_efficiency': (perf.get('html_files_generated', 0) / perf.get('total_processing_time', 1)) if perf.get('total_processing_time', 0) > 0 else 0
                    })
                
                # Existing detailed timing analysis
                if timing_logs.get('performance_metrics'):
                    perf = timing_logs['performance_metrics']
                    timing_analysis.append({
                        'test_id': test_id,
                        'mode': mode,
                        'url_count': url_count,
                        'total_time': perf.get('total_processing_time', 0),
                        'avg_time_per_url': perf.get('average_time_per_url', 0),
                        'avg_time_per_level': perf.get('average_time_per_level', 0),
                        'urls_processed': perf.get('urls_processed', 0),
                        'urls_from_cache': perf.get('urls_from_cache', 0),
                        'cache_efficiency_percent': perf.get('cache_efficiency_percent', 0),
                        'html_files_generated': perf.get('html_files_generated', 0),
                        'clusters_generated': perf.get('clusters_generated', 0)
                    })
                
                # Cache efficiency data
                if timing_logs.get('performance_metrics'):
                    perf = timing_logs['performance_metrics']
                    cache_efficiency.append({
                        'test_id': test_id,
                        'mode': mode,
                        'url_count': url_count,
                        'cache_efficiency': perf.get('cache_efficiency_percent', 0),
                        'urls_from_cache': perf.get('urls_from_cache', 0),
                        'urls_newly_processed': perf.get('urls_newly_processed', 0),
                        'cache_savings': perf.get('cache_savings', 'N/A')
                    })
                
                # Step-by-step timing data
                if timing_logs.get('steps'):
                    for step_name, step_data in timing_logs['steps'].items():
                        step_timing.append({
                            'test_id': test_id,
                            'mode': mode,
                            'step_name': step_name,
                            'duration': step_data.get('duration', 0),
                            'description': step_data.get('description', ''),
                            'urls_processed': step_data.get('urls_processed', 0),
                            'cache_type': step_data.get('cache_type', 'none')
                        })
                
                # Cluster count data
                clustering_results = result.get('clustering_results', [])
                for cluster_result in clustering_results:
                    if cluster_result.get('cluster_summary'):
                        cluster_counts.append({
                            'test_id': test_id,
                            'mode': mode,
                            'level': cluster_result.get('level', 0),
                            'cluster_count': cluster_result['cluster_summary'].get('num_clusters', 0),
                            'dbcv_score': cluster_result['cluster_summary'].get('dbcv_score', 0)
                        })
                
                # HTML files count
                html_files_summary = result.get('html_files_summary', {})
                html_count = html_files_summary.get('count', len(result.get('html_files', [])))
                html_file_counts.append({
                    'test_id': test_id,
                    'mode': mode,
                    'html_count': html_count
                })
        
        # Generate mode comparison metrics
        mode_0_results = [r for r in comprehensive_experiment_metrics if r['mode'] == 0]
        mode_1_results = [r for r in comprehensive_experiment_metrics if r['mode'] == 1]
        
        for url_count in set(r['url_count'] for r in comprehensive_experiment_metrics):
            mode_0_subset = [r for r in mode_0_results if r['url_count'] == url_count]
            mode_1_subset = [r for r in mode_1_results if r['url_count'] == url_count]
            
            if mode_0_subset and mode_1_subset:
                mode_comparison_metrics.append({
                    'url_count': url_count,
                    'mode_0_avg_time': sum(r['total_time'] for r in mode_0_subset) / len(mode_0_subset),
                    'mode_1_avg_time': sum(r['total_time'] for r in mode_1_subset) / len(mode_1_subset),
                    'mode_0_avg_cache_efficiency': sum(r['cache_efficiency'] for r in mode_0_subset) / len(mode_0_subset),
                    'mode_1_avg_cache_efficiency': sum(r['cache_efficiency'] for r in mode_1_subset) / len(mode_1_subset),
                    'mode_0_avg_clusters': sum(r['clusters_generated'] for r in mode_0_subset) / len(mode_0_subset),
                    'mode_1_avg_clusters': sum(r['clusters_generated'] for r in mode_1_subset) / len(mode_1_subset),
                    'mode_0_tests': len(mode_0_subset),
                    'mode_1_tests': len(mode_1_subset)
                })
        
        print(f"📈 Generated metrics:")
        print(f"   🌐 URL processing times: {len(url_processing_times)} entries")
        print(f"   🎯 Clustering times by level: {len(clustering_times_by_level)} entries")
        print(f"   🔍 Similarity analysis times: {len(similarity_analysis_times)} entries")
        print(f"   📊 Level performance breakdown: {len(level_performance_breakdown)} entries")
        print(f"   ⚖️ Mode comparison metrics: {len(mode_comparison_metrics)} entries")
        print(f"   📋 Comprehensive metrics: {len(comprehensive_experiment_metrics)} entries")
        
        # ===============================================
        # CONFIGURABLE SECTION: DATA FILE GENERATION
        # ===============================================
        # Save basic data files (controlled by GENERATE_BASIC_DATA configuration)
        files_saved = 0
        print(f"\n💾 Saving data files...")
        
        if GENERATE_BASIC_DATA.get('processing_times', False):
            self.save_gnuplot_data_file(processing_times, os.path.join(gnuplot_dir, "processing_times.dat"))
            print(f"   ✅ processing_times.dat ({len(processing_times)} entries)")
            files_saved += 1
        
        if GENERATE_BASIC_DATA.get('cluster_counts', False):
            self.save_gnuplot_data_file(cluster_counts, os.path.join(gnuplot_dir, "cluster_counts.dat"))
            print(f"   ✅ cluster_counts.dat ({len(cluster_counts)} entries)")
            files_saved += 1
            
        if GENERATE_BASIC_DATA.get('html_file_counts', False):
            self.save_gnuplot_data_file(html_file_counts, os.path.join(gnuplot_dir, "html_file_counts.dat"))
            print(f"   ✅ html_file_counts.dat ({len(html_file_counts)} entries)")
            files_saved += 1
            
        if GENERATE_BASIC_DATA.get('timing_analysis', False):
            self.save_gnuplot_data_file(timing_analysis, os.path.join(gnuplot_dir, "timing_analysis.dat"))
            print(f"   ✅ timing_analysis.dat ({len(timing_analysis)} entries)")
            files_saved += 1
            
        if GENERATE_BASIC_DATA.get('cache_efficiency', False):
            self.save_gnuplot_data_file(cache_efficiency, os.path.join(gnuplot_dir, "cache_efficiency.dat"))
            print(f"   ✅ cache_efficiency.dat ({len(cache_efficiency)} entries)")
            files_saved += 1
            
        if GENERATE_BASIC_DATA.get('step_timing', False):
            self.save_gnuplot_data_file(step_timing, os.path.join(gnuplot_dir, "step_timing.dat"))
            print(f"   ✅ step_timing.dat ({len(step_timing)} entries)")
            files_saved += 1
        
        # Save enhanced metrics files (controlled by GENERATE_ENHANCED_DATA configuration)
        if GENERATE_ENHANCED_DATA.get('url_processing_times', False):
            self.save_gnuplot_data_file(url_processing_times, os.path.join(gnuplot_dir, "url_processing_times.dat"))
            print(f"   ✅ url_processing_times.dat ({len(url_processing_times)} entries)")
            files_saved += 1
            
        if GENERATE_ENHANCED_DATA.get('clustering_times_by_level', False):
            self.save_gnuplot_data_file(clustering_times_by_level, os.path.join(gnuplot_dir, "clustering_times_by_level.dat"))
            print(f"   ✅ clustering_times_by_level.dat ({len(clustering_times_by_level)} entries)")
            files_saved += 1
            
        if GENERATE_ENHANCED_DATA.get('similarity_analysis_times', False):
            self.save_gnuplot_data_file(similarity_analysis_times, os.path.join(gnuplot_dir, "similarity_analysis_times.dat"))
            print(f"   ✅ similarity_analysis_times.dat ({len(similarity_analysis_times)} entries)")
            files_saved += 1
            
        if GENERATE_ENHANCED_DATA.get('level_performance_breakdown', False):
            self.save_gnuplot_data_file(level_performance_breakdown, os.path.join(gnuplot_dir, "level_performance_breakdown.dat"))
            print(f"   ✅ level_performance_breakdown.dat ({len(level_performance_breakdown)} entries)")
            files_saved += 1
            
        if GENERATE_ENHANCED_DATA.get('mode_comparison_metrics', False):
            self.save_gnuplot_data_file(mode_comparison_metrics, os.path.join(gnuplot_dir, "mode_comparison_metrics.dat"))
            print(f"   ✅ mode_comparison_metrics.dat ({len(mode_comparison_metrics)} entries)")
            files_saved += 1
            
        if GENERATE_ENHANCED_DATA.get('comprehensive_experiment_metrics', False):
            self.save_gnuplot_data_file(comprehensive_experiment_metrics, os.path.join(gnuplot_dir, "comprehensive_experiment_metrics.dat"))
            print(f"   ✅ comprehensive_experiment_metrics.dat ({len(comprehensive_experiment_metrics)} entries)")
            files_saved += 1
        
        print(f"💾 Saved {files_saved} data files to {gnuplot_dir}")
        
        # ===============================================
        # CONFIGURABLE SECTION: SCRIPT GENERATION & IMMEDIATE PNG CREATION
        # ===============================================
        # Create gnuplot scripts and automatically execute them to generate PNG images
        print(f"🎨 Generating gnuplot scripts and PNG images...")
        
        # Quick gnuplot availability check
        if AUTO_EXECUTE_GNUPLOT:
            try:
                import subprocess
                gnuplot_check = subprocess.run(['which', 'gnuplot'], capture_output=True, text=True, timeout=5)
                if gnuplot_check.returncode == 0:
                    print(f"✅ Gnuplot available: {gnuplot_check.stdout.strip()}")
                else:
                    print(f"⚠️ Gnuplot not found - will attempt auto-installation during execution")
            except:
                print(f"⚠️ Could not verify gnuplot - continuing anyway")
        
        generated_images, execution_log = self.create_gnuplot_scripts(gnuplot_dir, GENERATE_SCRIPTS, OUTPUT_FORMATS, AUTO_EXECUTE_GNUPLOT)
        
        # Enhanced feedback about generated images
        if generated_images:
            print(f"📈 Successfully generated {len(generated_images)} PNG images:")
            for img in generated_images:
                print(f"   🖼️  {img['filename']} ({img['size_kb']:.1f} KB) - {img['chart_type']}")
        else:
            print(f"⚠️ No PNG images were generated. Check execution log for issues.")
            
        return generated_images, execution_log
    
    def save_gnuplot_data_file(self, data: List[Dict], filename: str, auto_generate_image: bool = True):
        """Save data in gnuplot-friendly format and optionally generate image immediately"""
        if not data:
            return
        
        with open(filename, 'w') as f:
            # Write header
            if data:
                headers = list(data[0].keys())
                f.write("# " + "\t".join(headers) + "\n")
                
                # Write data
                for row in data:
                    values = [str(row.get(header, '')) for header in headers]
                    f.write("\t".join(values) + "\n")
        
        print(f"💾 Saved: {os.path.basename(filename)} ({len(data)} entries)")
        
        # Immediately generate image if requested
        if auto_generate_image:
            self.generate_immediate_image(filename, data)
    
    def generate_immediate_image(self, data_filename: str, data: List[Dict]):
        """Generate PNG image immediately after saving a .dat file"""
        import subprocess
        import os
        
        # Get the directory and base filename
        data_dir = os.path.dirname(data_filename)
        base_name = os.path.basename(data_filename).replace('.dat', '')
        
        # Create generated_images directory if it doesn't exist
        images_dir = os.path.join(data_dir, "generated_images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate appropriate script based on data type
        script_content = self.create_script_for_data_type(base_name, data)
        
        if not script_content:
            return  # No script generated for this data type
            
        # Save the script
        script_filename = os.path.join(data_dir, f"{base_name}_immediate.gnuplot")
        with open(script_filename, 'w') as f:
            f.write(script_content)
        
        # Execute the script immediately
        try:
            original_dir = os.getcwd()
            os.chdir(data_dir)
            
            result = subprocess.run(['gnuplot', f"{base_name}_immediate.gnuplot"], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                image_filename = f"{base_name}.png"
                image_path = os.path.join("generated_images", image_filename)
                
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    print(f"🖼️  Generated: {image_filename} ({file_size/1024:.1f} KB)")
                else:
                    print(f"⚠️  Script executed but no image found: {image_filename}")
            else:
                print(f"❌ Failed to generate image for {base_name}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  Timeout generating image for {base_name}")
        except FileNotFoundError:
            print(f"❌ Gnuplot not found - install with: sudo apt install gnuplot")
        except Exception as e:
            print(f"❌ Error generating image for {base_name}: {e}")
        finally:
            os.chdir(original_dir)
    
    def create_script_for_data_type(self, data_type: str, data: List[Dict]) -> str:
        """Create appropriate gnuplot script based on data type"""
        
        if data_type == "processing_times":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/processing_times.png'
set title 'Processing Time Comparison by Mode\\nGenerated immediately after data creation'
set xlabel 'URL Count'
set ylabel 'Processing Time (seconds)'
set grid
set key top left
set style data linespoints
set pointsize 1.5

plot 'processing_times.dat' using 4:($2==0?$5:1/0) with linespoints title 'Mode 0 (All Together)' pt 7 lc rgb 'blue', \\
     'processing_times.dat' using 4:($2==1?$5:1/0) with linespoints title 'Mode 1 (Domain-based)' pt 5 lc rgb 'red'
"""
        
        elif data_type == "cluster_counts":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/cluster_counts.png'
set title 'Clustering Results by DOM Level\\nGenerated immediately after data creation'
set xlabel 'DOM Level'
set ylabel 'Number of Clusters'
set grid
set key top right

plot 'cluster_counts.dat' using 3:($2==0?$4:1/0) with linespoints title 'Mode 0' pt 7 lc rgb 'blue', \\
     'cluster_counts.dat' using 3:($2==1?$4:1/0) with linespoints title 'Mode 1' pt 5 lc rgb 'red'
"""
        
        elif data_type == "cache_efficiency":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/cache_efficiency.png'
set title 'Cache Efficiency Analysis\\nGenerated immediately after data creation'
set xlabel 'URL Count'
set ylabel 'Cache Efficiency (%)'
set grid
set key top right
set yrange [0:100]

plot 'cache_efficiency.dat' using 3:($2==0?$4:1/0) with linespoints title 'Mode 0 Cache Efficiency' pt 7 lc rgb 'green', \\
     'cache_efficiency.dat' using 3:($2==1?$4:1/0) with linespoints title 'Mode 1 Cache Efficiency' pt 5 lc rgb 'orange'
"""
        
        elif data_type == "timing_analysis":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/timing_analysis.png'
set title 'Detailed Timing Analysis\\nGenerated immediately after data creation'
set xlabel 'URL Count'
set ylabel 'Time (seconds)'
set grid
set key top left
set logscale y

plot 'timing_analysis.dat' using 3:($2==0?$5:1/0) with linespoints title 'Mode 0 - Avg per URL' pt 7 lc rgb 'blue', \\
     'timing_analysis.dat' using 3:($2==1?$5:1/0) with linespoints title 'Mode 1 - Avg per URL' pt 5 lc rgb 'red'
"""
        
        elif data_type == "html_file_counts":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/html_file_counts.png'
set title 'HTML Files Generated per Test\\nGenerated immediately after data creation'
set xlabel 'Test Case Index'
set ylabel 'HTML Files Count'
set grid
set key top left

plot 'html_file_counts.dat' using 0:($2==0?$3:1/0) with impulses title 'Mode 0' lc rgb 'blue', \\
     'html_file_counts.dat' using 0:($2==1?$3:1/0) with impulses title 'Mode 1' lc rgb 'red'
"""
        
        elif data_type == "clustering_times_by_level":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/clustering_times_by_level.png'
set title 'Clustering Performance by Level\\nGenerated immediately after data creation'
set xlabel 'DOM Level'
set ylabel 'Clustering Time (seconds)'
set grid
set key top left

plot 'clustering_times_by_level.dat' using 3:($2==0?$6:1/0) with linespoints title 'Mode 0 Total Clustering Time' pt 7 lc rgb 'blue', \\
     'clustering_times_by_level.dat' using 3:($2==1?$6:1/0) with linespoints title 'Mode 1 Total Clustering Time' pt 5 lc rgb 'red'
"""
        
        elif data_type == "url_processing_times":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/url_processing_times.png'
set title 'URL Processing Time Distribution\\nGenerated immediately after data creation'
set xlabel 'URL Index'
set ylabel 'Processing Time (seconds)'
set grid
set key top left

plot 'url_processing_times.dat' using 3:($2==0?$7:1/0) with points title 'Mode 0' pt 7 lc rgb 'blue', \\
     'url_processing_times.dat' using 3:($2==1?$7:1/0) with points title 'Mode 1' pt 5 lc rgb 'red'
"""
        
        elif data_type == "mode_comparison_metrics":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/mode_comparison_metrics.png'
set title 'Mode 0 vs Mode 1 Performance Comparison\\nGenerated immediately after data creation'
set xlabel 'URL Count'
set ylabel 'Average Processing Time (seconds)'
set grid
set key top left

plot 'mode_comparison_metrics.dat' using 1:2 with linespoints title 'Mode 0 Average Time' pt 7 lc rgb 'blue', \\
     'mode_comparison_metrics.dat' using 1:3 with linespoints title 'Mode 1 Average Time' pt 5 lc rgb 'red'
"""
        
        elif data_type == "comprehensive_experiment_metrics":
            return """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/comprehensive_experiment_metrics.png'
set title 'Comprehensive Experiment Metrics\\nGenerated immediately after data creation'
set xlabel 'URL Count'
set ylabel 'Processing Time (seconds)'
set grid
set key top left

plot 'comprehensive_experiment_metrics.dat' using 3:($2==0?$5:1/0) with linespoints title 'Mode 0 Total Time' pt 7 lc rgb 'blue', \\
     'comprehensive_experiment_metrics.dat' using 3:($2==1?$5:1/0) with linespoints title 'Mode 1 Total Time' pt 5 lc rgb 'red'
"""
        
        else:
            # Generic plot for unrecognized data types
            if data and len(data) > 0:
                headers = list(data[0].keys())
                if len(headers) >= 2:
                    return f"""#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/{data_type}.png'
set title 'Data Visualization: {data_type.replace("_", " ").title()}\\nGenerated immediately after data creation'
set xlabel '{headers[0].replace("_", " ").title()}'
set ylabel '{headers[1].replace("_", " ").title()}'
set grid
set key top left

plot '{data_type}.dat' using 1:2 with linespoints title '{data_type.replace("_", " ").title()}' pt 7 lc rgb 'blue'
"""
        
        return None  # No script for this data type
    
    def create_gnuplot_scripts(self, gnuplot_dir: str, generate_scripts: dict, output_formats: list, auto_execute: bool):
        """
        Create sample gnuplot scripts for visualization and generate images
        
        Args:
            gnuplot_dir: Directory to save scripts and images
            generate_scripts: Dictionary of script types to generate (from configuration)
            output_formats: List of output formats (from configuration)
            auto_execute: Whether to automatically execute generated scripts
        """
        
        # Create subdirectory for generated images
        images_dir = os.path.join(gnuplot_dir, "generated_images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Use the configured output formats
        scripts_and_formats = output_formats
        
        scripts_created = 0
        print(f"\n🎨 Generating gnuplot scripts...")
        
        # Check which data files actually exist to avoid script generation errors
        existing_data_files = {
            'processing_times': os.path.exists(os.path.join(gnuplot_dir, 'processing_times.dat')),
            'cluster_counts': os.path.exists(os.path.join(gnuplot_dir, 'cluster_counts.dat')),
            'cache_efficiency': os.path.exists(os.path.join(gnuplot_dir, 'cache_efficiency.dat')),
            'timing_analysis': os.path.exists(os.path.join(gnuplot_dir, 'timing_analysis.dat')),
            'clustering_times_by_level': os.path.exists(os.path.join(gnuplot_dir, 'clustering_times_by_level.dat')),
            'html_file_counts': os.path.exists(os.path.join(gnuplot_dir, 'html_file_counts.dat'))
        }
        
        print(f"📊 Available data files: {sum(existing_data_files.values())}/{len(existing_data_files)}")
        for file_name, exists in existing_data_files.items():
            print(f"   {'✅' if exists else '❌'} {file_name}.dat")
        
        for format_ext, terminal_cmd in scripts_and_formats:
            # ===============================================
            # CONFIGURABLE SECTION: PROCESSING TIME PLOTS
            # ===============================================
            if generate_scripts.get('processing_time_plots', False) and existing_data_files['processing_times']:
                script_content = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/processing_time_by_mode.{format_ext}'
set title 'Web Scraping Processing Time Analysis: Mode Comparison\\nData: Total processing time (seconds) for URL clustering analysis'
set xlabel 'URL Count'
set ylabel 'Processing Time (seconds)'
set grid
set key top left
set style data points
set pointsize 1.5

plot 'processing_times.dat' using 4:($2==0?$5:1/0) with linespoints title 'Mode 0 (All Together)' pt 7 lc rgb 'blue', \\
     'processing_times.dat' using 4:($2==1?$5:1/0) with linespoints title 'Mode 1 (Domain-based)' pt 5 lc rgb 'red'
"""
                
                with open(os.path.join(gnuplot_dir, f"processing_time_plot_{format_ext}.gnuplot"), 'w') as f:
                    f.write(script_content)
                    
                if format_ext == scripts_and_formats[0][0]:  # Only print once
                    print(f"   ✅ Processing time plots")
                    scripts_created += 1
            
            # ===============================================
            # CONFIGURABLE SECTION: CLUSTER COUNT PLOTS
            # ===============================================
            if generate_scripts.get('cluster_count_plots', False) and existing_data_files['cluster_counts']:
                cluster_script = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/clusters_by_level.{format_ext}'
set title 'HDBSCAN Clustering Results by DOM Tree Depth\\nData: Number of clusters generated using HDBSCAN algorithm'
set xlabel 'DOM Level'
set ylabel 'Number of Clusters'
set grid
set key top right

plot 'cluster_counts.dat' using 3:($2==0?$4:1/0) with linespoints title 'Mode 0' pt 7 lc rgb 'blue', \\
     'cluster_counts.dat' using 3:($2==1?$4:1/0) with linespoints title 'Mode 1' pt 5 lc rgb 'red'
"""
                
                with open(os.path.join(gnuplot_dir, f"cluster_count_plot_{format_ext}.gnuplot"), 'w') as f:
                    f.write(cluster_script)
                    
                if format_ext == scripts_and_formats[0][0]:  # Only print once
                    print(f"   ✅ Cluster count plots")
                    scripts_created += 1
            
            # ===============================================
            # CONFIGURABLE SECTION: CACHE EFFICIENCY PLOTS
            # ===============================================
            if generate_scripts.get('cache_efficiency_plots', False) and existing_data_files['cache_efficiency']:
                cache_script = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/cache_efficiency_analysis.{format_ext}'
set title 'Cache System Efficiency Analysis\\nData: Percentage of URLs served from cache vs processed'
set xlabel 'URL Count'
set ylabel 'Cache Efficiency (%)'
set grid
set key top right
set yrange [0:100]

plot 'cache_efficiency.dat' using 3:($2==0?$4:1/0) with linespoints title 'Mode 0 Cache Efficiency' pt 7 lc rgb 'green', \\
     'cache_efficiency.dat' using 3:($2==1?$4:1/0) with linespoints title 'Mode 1 Cache Efficiency' pt 5 lc rgb 'orange'
"""
                
                with open(os.path.join(gnuplot_dir, f"cache_efficiency_plot_{format_ext}.gnuplot"), 'w') as f:
                    f.write(cache_script)
                    
                if format_ext == scripts_and_formats[0][0]:  # Only print once
                    print(f"   ✅ Cache efficiency plots")
                    scripts_created += 1
            
            # ===============================================
            # CONFIGURABLE SECTION: TIMING ANALYSIS PLOTS
            # ===============================================
            if generate_scripts.get('timing_analysis_plots', False) and existing_data_files['timing_analysis']:
                timing_script = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/detailed_timing_analysis.{format_ext}'
set title 'Detailed Processing Time Breakdown\\nData: Average time per URL and per DOM level'
set xlabel 'URL Count'
set ylabel 'Time (seconds)'
set grid
set key top left
set logscale y

plot 'timing_analysis.dat' using 3:($2==0?$5:1/0) with linespoints title 'Mode 0 - Avg per URL' pt 7 lc rgb 'blue', \\
     'timing_analysis.dat' using 3:($2==1?$5:1/0) with linespoints title 'Mode 1 - Avg per URL' pt 5 lc rgb 'red', \\
     'timing_analysis.dat' using 3:($2==0?$6:1/0) with linespoints title 'Mode 0 - Avg per Level' pt 9 lc rgb 'cyan', \\
     'timing_analysis.dat' using 3:($2==1?$6:1/0) with linespoints title 'Mode 1 - Avg per Level' pt 11 lc rgb 'magenta'
"""
                
                with open(os.path.join(gnuplot_dir, f"timing_analysis_plot_{format_ext}.gnuplot"), 'w') as f:
                    f.write(timing_script)
                    
                if format_ext == scripts_and_formats[0][0]:  # Only print once
                    print(f"   ✅ Timing analysis plots")
                    scripts_created += 1
            
            # ===============================================
            # CONFIGURABLE SECTION: PERFORMANCE DASHBOARD
            # ===============================================
            if generate_scripts.get('performance_dashboard', False) and existing_data_files['processing_times']:
                # Create a flexible dashboard that adapts to available data
                dashboard_charts = []
                
                # Chart 1: Always include processing time if available
                dashboard_charts.append("""
# Chart 1: Processing Time Comparison
set title 'Processing Time by Mode'
set xlabel 'URL Count'
set ylabel 'Time (seconds)'
set grid
plot 'processing_times.dat' using 4:($2==0?$5:1/0) with linespoints title 'Mode 0' pt 7 lc rgb 'blue', \\
     'processing_times.dat' using 4:($2==1?$5:1/0) with linespoints title 'Mode 1' pt 5 lc rgb 'red'""")
                
                # Chart 2: Cache efficiency if available
                if existing_data_files['cache_efficiency']:
                    dashboard_charts.append("""
# Chart 2: Cache Efficiency
set title 'Cache Efficiency'
set xlabel 'URL Count'
set ylabel 'Efficiency (%)'
set yrange [0:100]
plot 'cache_efficiency.dat' using 3:4 with linespoints title 'Cache Hit Rate' pt 9 lc rgb 'green'""")
                else:
                    dashboard_charts.append("""
# Chart 2: Processing Time Distribution
set title 'Processing Time Distribution'
set xlabel 'Test Case'
set ylabel 'Time (seconds)'
set grid
plot 'processing_times.dat' using 0:5 with impulses title 'Processing Times' lc rgb 'green'""")
                
                # Chart 3: Clustering results if available, otherwise processing time by mode
                if existing_data_files['cluster_counts']:
                    dashboard_charts.append("""
# Chart 3: Clustering Quality
set title 'Clustering Results'
set xlabel 'DOM Level'
set ylabel 'Cluster Count'
set yrange [0:*]
plot 'cluster_counts.dat' using 3:4 with linespoints title 'Clusters Generated' pt 7 lc rgb 'purple'""")
                else:
                    dashboard_charts.append("""
# Chart 3: Mode Comparison
set title 'Mode 0 vs Mode 1 Performance'
set xlabel 'URL Count'
set ylabel 'Time (seconds)'
set grid
set style fill solid
plot 'processing_times.dat' using 4:($2==0?$5:1/0) with boxes title 'Mode 0' lc rgb 'blue', \\
     'processing_times.dat' using 4:($2==1?$5:1/0) with boxes title 'Mode 1' lc rgb 'red'""")
                
                # Chart 4: HTML files if available, otherwise URL count vs time
                if existing_data_files['html_file_counts']:
                    dashboard_charts.append("""
# Chart 4: HTML Output
set title 'HTML Files Generated'
set xlabel 'Test Case'
set ylabel 'File Count'
plot 'html_file_counts.dat' using 0:3 with impulses title 'HTML Files' lc rgb 'orange'""")
                else:
                    dashboard_charts.append("""
# Chart 4: URL Count vs Processing Time
set title 'Scalability Analysis'
set xlabel 'URL Count'
set ylabel 'Time (seconds)'
set grid
set logscale y
plot 'processing_times.dat' using 4:5 with points title 'All Tests' pt 7 lc rgb 'orange'""")
                
                # Create the dashboard script
                chart_count = len(dashboard_charts)
                layout = "2,2" if chart_count == 4 else f"2,{(chart_count+1)//2}"
                
                dashboard_script = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/performance_dashboard.{format_ext}'
set multiplot layout {layout} title 'Performance Analysis Dashboard'

{''.join(dashboard_charts)}

unset multiplot
"""
                
                with open(os.path.join(gnuplot_dir, f"performance_dashboard_{format_ext}.gnuplot"), 'w') as f:
                    f.write(dashboard_script)
                    
                if format_ext == scripts_and_formats[0][0]:  # Only print once
                    print(f"   ✅ Performance dashboard")
                    scripts_created += 1
                    
            # ===============================================
            # CONFIGURABLE SECTION: DOMAIN-SPECIFIC PLOTS (Mode 1)
            # ===============================================
            if generate_scripts.get('domain_specific_plots', False) and existing_data_files['clustering_times_by_level']:
                domain_script = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/domain_specific_analysis.{format_ext}'
set multiplot layout 2,2 title 'Mode 1 Domain-Specific Performance Analysis'

# Chart 1: Processing Time by Domain
set title 'Processing Time by Domain (Mode 1)'
set xlabel 'Domain'
set ylabel 'Processing Time (seconds)'
set grid
set xtics rotate by -45
plot 'clustering_times_by_level.dat' using (stringcolumn(3)):($2==1?$6:1/0):xtic(3) with boxes title 'Clustering Time' lc rgb 'blue'

# Chart 2: Clustering Quality by Domain
set title 'Clustering Quality (DBCV Score) by Domain'
set xlabel 'Domain'
set ylabel 'DBCV Score'
set yrange [-0.2:1]
set grid
plot 'clustering_times_by_level.dat' using (stringcolumn(3)):($2==1?$10:1/0):xtic(3) with boxes title 'DBCV Score' lc rgb 'green'

# Chart 3: Clusters Generated by Domain
set title 'Number of Clusters by Domain'
set xlabel 'Domain'
set ylabel 'Clusters Count'
set grid
plot 'clustering_times_by_level.dat' using (stringcolumn(3)):($2==1?$9:1/0):xtic(3) with boxes title 'Clusters Generated' lc rgb 'red'

# Chart 4: File Processing Efficiency
set title 'File Processing Efficiency by Domain'
set xlabel 'Domain'
set ylabel 'File Size (MB) vs Time Ratio'
set grid
plot 'clustering_times_by_level.dat' using (stringcolumn(3)):($2==1?($8/$6):1/0):xtic(3) with boxes title 'MB/Second' lc rgb 'purple'

unset multiplot
"""
                
                with open(os.path.join(gnuplot_dir, f"domain_analysis_plot_{format_ext}.gnuplot"), 'w') as f:
                    f.write(domain_script)
                    
                # Additional detailed domain comparison script
                domain_comparison_script = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/mode_domain_comparison.{format_ext}'
set title 'Mode 0 vs Mode 1: Domain Processing Comparison\\nData: Processing time and efficiency comparison between unified and domain-based processing'
set xlabel 'URL Count'
set ylabel 'Processing Time (seconds)'
set grid
set key top left
set style data linespoints
set pointsize 1.5

# Plot both overall Mode 0/1 and individual domains from Mode 1
plot 'processing_times.dat' using 4:($2==0?$5:1/0) with linespoints title 'Mode 0 (Unified)' pt 7 lc rgb 'blue', \\
     'processing_times.dat' using 4:($2==1&&!stringcolumn(3)?$5:1/0) with linespoints title 'Mode 1 (Overall)' pt 5 lc rgb 'red', \\
     'processing_times.dat' using 4:(stringcolumn(3)=="dia-trofis.gr"?$5:1/0) with linespoints title 'dia-trofis.gr (Domain)' pt 9 lc rgb 'green', \\
     'processing_times.dat' using 4:(stringcolumn(3)=="gastronomos.gr"?$5:1/0) with linespoints title 'gastronomos.gr (Domain)' pt 11 lc rgb 'orange'
"""
                
                with open(os.path.join(gnuplot_dir, f"mode_domain_comparison_{format_ext}.gnuplot"), 'w') as f:
                    f.write(domain_comparison_script)
                    
                if format_ext == scripts_and_formats[0][0]:  # Only print once
                    print(f"   ✅ Domain-specific plots")
                    scripts_created += 1
        
        print(f"🎨 Generated {scripts_created} script types in {len(scripts_and_formats)} formats")
        
        if scripts_created == 0:
            print(f"⚠️ No scripts were generated! Possible causes:")
            print(f"   - Missing data files (check above)")
            print(f"   - All script types disabled in configuration")
            print(f"   - Data files exist but scripts are disabled")
            
            # Generate at least a basic processing time script if the data exists
            if existing_data_files['processing_times']:
                print(f"🔧 Generating fallback processing time script...")
                fallback_script = f"""#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'generated_images/processing_time_fallback.png'
set title 'Processing Time Analysis (Fallback)'
set xlabel 'URL Count'
set ylabel 'Processing Time (seconds)'
set grid
set key top left

plot 'processing_times.dat' using 4:5 with linespoints title 'All Tests' pt 7 lc rgb 'blue'
"""
                with open(os.path.join(gnuplot_dir, "fallback_processing_time_png.gnuplot"), 'w') as f:
                    f.write(fallback_script)
                print(f"   ✅ Created fallback script: fallback_processing_time_png.gnuplot")
                scripts_created += 1
        
        # ===============================================
        # CONFIGURABLE SECTION: SCRIPT EXECUTION
        # ===============================================
        # Optionally execute gnuplot scripts automatically
        if auto_execute:
            print(f"⚡ Auto-executing gnuplot scripts...")
            generated_images, execution_log = self.execute_gnuplot_scripts(gnuplot_dir)
        else:
            print(f"⏸️  Script execution disabled - scripts created but not executed")
            generated_images, execution_log = [], ["Script execution disabled by configuration"]
            
        return generated_images, execution_log
    
    def execute_gnuplot_scripts(self, gnuplot_dir: str):
        """Execute gnuplot scripts to generate images"""
        import subprocess
        import glob
        
        generated_images = []
        execution_log = []
        
        try:
            # Check if gnuplot is available
            gnuplot_check = subprocess.run(['which', 'gnuplot'], 
                                         capture_output=True, 
                                         text=True, 
                                         timeout=5)
            
            if gnuplot_check.returncode != 0:
                print("🔧 Gnuplot not found, attempting to install...")
                execution_log.append("Gnuplot not found, attempting to install...")
                
                # Try to install gnuplot (simplified approach)
                try:
                    # First update package list
                    update_result = subprocess.run(['sudo', 'apt', 'update'], 
                                                 capture_output=True, 
                                                 text=True, 
                                                 timeout=120)
                    
                    if update_result.returncode == 0:
                        # Then install gnuplot
                        install_result = subprocess.run(['sudo', 'apt', 'install', '-y', 'gnuplot'], 
                                                      capture_output=True, 
                                                      text=True, 
                                                      timeout=300)
                        
                        if install_result.returncode == 0:
                            print("✅ Gnuplot installed successfully!")
                            execution_log.append("Gnuplot installed successfully!")
                        else:
                            print("⚠️ Failed to install gnuplot automatically")
                            execution_log.append(f"Failed to install gnuplot: {install_result.stderr}")
                            print("📝 Manual installation: sudo apt install gnuplot")
                            execution_log.append("Manual installation required: sudo apt install gnuplot")
                            # Continue anyway - maybe it's available in a different location
                    else:
                        print("⚠️ Failed to update package list")
                        execution_log.append(f"Failed to update package list: {update_result.stderr}")
                        
                except Exception as e:
                    print(f"⚠️ Error installing gnuplot: {e}")
                    execution_log.append(f"Error installing gnuplot: {e}")
                    # Continue anyway - maybe gnuplot is available but not in PATH
            
            # Change to gnuplot directory
            original_dir = os.getcwd()
            os.chdir(gnuplot_dir)
            
            # Ensure generated_images directory exists
            images_subdir = "generated_images"
            if not os.path.exists(images_subdir):
                os.makedirs(images_subdir)
                print(f"📁 Created images directory: {images_subdir}")
                execution_log.append(f"Created images directory: {images_subdir}")
            
            # Find all gnuplot scripts
            gnuplot_scripts = glob.glob("*.gnuplot")
            execution_log.append(f"Found {len(gnuplot_scripts)} gnuplot scripts")
            print(f"📊 Found {len(gnuplot_scripts)} gnuplot scripts to execute")
            
            if not gnuplot_scripts:
                print(f"⚠️ No gnuplot scripts found in {gnuplot_dir}")
                execution_log.append(f"No gnuplot scripts found in {gnuplot_dir}")
                return [], execution_log
            
            for script in gnuplot_scripts:
                try:
                    print(f"🎯 Executing {script}...")
                    execution_log.append(f"Executing {script}")
                    
                    # Try to execute the script
                    result = subprocess.run(['gnuplot', script], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=60)
                    
                    if result.returncode == 0:
                        print(f"✅ Successfully executed {script}")
                        execution_log.append(f"Successfully executed {script}")
                        
                        # Check for newly generated images immediately after script execution
                        if os.path.exists(images_subdir):
                            current_images = [f for f in os.listdir(images_subdir) if f.endswith(('.png', '.ps', '.eps', '.svg', '.tex'))]
                            if current_images:
                                newest_image = max(current_images, key=lambda x: os.path.getmtime(os.path.join(images_subdir, x)))
                                print(f"   🖼️ Generated: {newest_image}")
                        
                        # List stdout/stderr for debugging
                        if result.stdout:
                            execution_log.append(f"Output: {result.stdout}")
                        if result.stderr:
                            execution_log.append(f"Warnings: {result.stderr}")
                        
                    else:
                        error_msg = f"Gnuplot script {script} failed (exit code {result.returncode}): {result.stderr}"
                        print(f"❌ {error_msg}")
                        execution_log.append(error_msg)
                        
                        # Show stdout too for debugging
                        if result.stdout:
                            execution_log.append(f"Stdout: {result.stdout}")
                        
                except subprocess.TimeoutExpired:
                    timeout_msg = f"Gnuplot script {script} timed out"
                    print(f"⏱️ {timeout_msg}")
                    execution_log.append(timeout_msg)
                except FileNotFoundError:
                    not_found_msg = "Gnuplot command not found"
                    print(f"❌ {not_found_msg}")
                    execution_log.append(not_found_msg)
                    break
                except Exception as e:
                    error_msg = f"Error executing {script}: {e}"
                    print(f"❌ {error_msg}")
                    execution_log.append(error_msg)
            
            # After all scripts are executed, collect all generated images
            # The images_dir is relative to where we're executing (gnuplot_dir)
            images_subdir = "generated_images"
            images_full_path = os.path.join(gnuplot_dir, images_subdir)
            
            print(f"📊 Scanning for generated images...")
            print(f"  Current working directory: {os.getcwd()}")
            print(f"  Looking for images in: {images_full_path}")
            execution_log.append(f"Scanning for generated images in {images_full_path}")
            
            if os.path.exists(images_subdir):
                print(f"✅ Found images directory: {images_subdir}")
                execution_log.append(f"Found images directory: {images_subdir}")
                
                for image_file in os.listdir(images_subdir):
                    if image_file.endswith(('.png', '.ps', '.eps', '.svg', '.tex')):
                        file_path = os.path.join(images_subdir, image_file)
                        file_size = os.path.getsize(file_path)
                        generated_images.append({
                            'filename': image_file,
                            'path': os.path.join("generated_images", image_file),
                            'size_bytes': file_size,
                            'size_kb': file_size / 1024,
                            'format': image_file.split('.')[-1].upper(),
                            'chart_type': image_file.split('.')[0].replace('_', ' ').title()
                        })
                        print(f"  📈 Found: {image_file} ({file_size} bytes)")
                        execution_log.append(f"Found image: {image_file} ({file_size} bytes)")
            else:
                print(f"⚠️ Images directory not found in current directory")
                print(f"  Trying absolute path: {images_full_path}")
                execution_log.append(f"Images directory not found in current directory")
                
                if os.path.exists(images_full_path):
                    print(f"✅ Found images directory at absolute path")
                    execution_log.append(f"Found images directory at absolute path")
                    
                    for image_file in os.listdir(images_full_path):
                        if image_file.endswith(('.png', '.ps', '.eps', '.svg', '.tex')):
                            file_path = os.path.join(images_full_path, image_file)
                            file_size = os.path.getsize(file_path)
                            generated_images.append({
                                'filename': image_file,
                                'path': os.path.join("generated_images", image_file),
                                'size_bytes': file_size,
                                'size_kb': file_size / 1024,
                                'format': image_file.split('.')[-1].upper(),
                                'chart_type': image_file.split('.')[0].replace('_', ' ').title()
                            })
                            print(f"  📈 Found: {image_file} ({file_size} bytes)")
                            execution_log.append(f"Found image: {image_file} ({file_size} bytes)")
                else:
                    print(f"❌ Images directory not found anywhere!")
                    execution_log.append(f"Images directory not found anywhere!")
            
            total_images = len(generated_images)
            print(f"🎉 Successfully generated {total_images} image files!")
            execution_log.append(f"Successfully generated {total_images} image files")
            
        except Exception as e:
            error_msg = f"Error in gnuplot execution: {e}"
            print(f"❌ {error_msg}")
            execution_log.append(error_msg)
        finally:
            # Always change back to original directory
            os.chdir(original_dir)
            
        return generated_images, execution_log
    
    def get_available_test_cases(self) -> List[Dict[str, Any]]:
        """Get all available test case combinations"""
        return self.generate_test_combinations()
    
    def filter_test_cases(self, test_cases: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter test cases based on criteria"""
        filtered = test_cases
        
        if 'priority' in filters:
            filtered = [tc for tc in filtered if tc['priority'] in filters['priority']]
        
        if 'max_duration' in filters:
            filtered = [tc for tc in filtered if tc['estimated_duration'] <= filters['max_duration']]
        
        if 'modes' in filters:
            filtered = [tc for tc in filtered if tc['mode'] in filters['modes']]
        
        if 'max_url_count' in filters:
            filtered = [tc for tc in filtered if tc['url_count'] <= filters['max_url_count']]
        
        return filtered 
    
    def _save_large_data_separately(self, results: List[Dict[str, Any]], experiment_dir: str) -> List[Dict[str, Any]]:
        """
        Aggressively save large data to separate files and return lightweight results.
        
        Args:
            results: List of result dictionaries
            experiment_dir: Directory to save files in
            
        Returns:
            List of lightweight result dictionaries with file references
        """
        lightweight_results = []
        large_data_dir = os.path.join(experiment_dir, "large_data")
        os.makedirs(large_data_dir, exist_ok=True)
        
        total_original_size = 0
        total_optimized_size = 0
        
        for i, result in enumerate(results):
            if result.get('status') != 'success':
                # Keep error results as-is
                lightweight_results.append(result)
                continue
                
            lightweight_result = {}
            test_id = result.get('test_metadata', {}).get('test_id', f'test_{i}')
            
            # Copy essential metadata only
            lightweight_result['status'] = result.get('status')
            lightweight_result['test_metadata'] = result.get('test_metadata', {})
            
            # PRESERVE timing_logs in lightweight result - this is essential for analysis
            if 'timing_logs' in result:
                lightweight_result['timing_logs'] = result['timing_logs']
            
            # Save clustering results with large cluster arrays separately
            if 'clustering_results' in result:
                clustering_file = os.path.join(large_data_dir, f"{test_id}_clustering_results.json")
                try:
                    # Calculate original size
                    clustering_original_size = len(json.dumps(result['clustering_results'], default=str).encode('utf-8'))
                    total_original_size += clustering_original_size
                    
                    with open(clustering_file, 'w') as f:
                        json.dump(result['clustering_results'], f, indent=2, default=str)
                    
                    # Create ultra-lightweight version - remove ALL large arrays
                    lightweight_clustering = []
                    for cluster_result in result['clustering_results']:
                        lightweight_cluster = {
                            'level': cluster_result.get('level'),
                            'status': cluster_result.get('status'),
                            'message': cluster_result.get('message'),
                            # Keep only cluster_info summary, NOT the full data
                            'cluster_summary': {
                                'num_clusters': cluster_result.get('cluster_info', {}).get('num_clusters', 0),
                                'dbcv_score': cluster_result.get('cluster_info', {}).get('dbcv_score', 0),
                                'min_cluster_size': cluster_result.get('cluster_info', {}).get('min_cluster_size', 0),
                                'useful_attributes_count': len(cluster_result.get('cluster_info', {}).get('useful_attributes', []))
                            },
                            'clusters_file': f"large_data/{test_id}_clustering_results.json",
                            'cluster_count': len(cluster_result.get('clusters', [])) if cluster_result.get('clusters') else 0
                        }
                        # Keep error information
                        if cluster_result.get('stack_trace'):
                            lightweight_cluster['stack_trace'] = cluster_result['stack_trace']
                        lightweight_clustering.append(lightweight_cluster)
                    
                    lightweight_result['clustering_results'] = lightweight_clustering
                    
                    # Calculate optimized size
                    clustering_optimized_size = len(json.dumps(lightweight_clustering, default=str).encode('utf-8'))
                    total_optimized_size += clustering_optimized_size
                    
                    print(f"📁 Clustering data: {clustering_original_size/1024:.1f}KB → {clustering_optimized_size/1024:.1f}KB")
                    
                except Exception as e:
                    print(f"❌ Failed to save clustering data: {e}")
                    # Keep original data if saving fails
                    lightweight_result['clustering_results'] = result.get('clustering_results', [])
            
            # Save processed clusters with large processed_data separately
            if 'processed_clusters' in result:
                processed_file = os.path.join(large_data_dir, f"{test_id}_processed_clusters.json")
                try:
                    # Calculate original size
                    processed_original_size = len(json.dumps(result['processed_clusters'], default=str).encode('utf-8'))
                    total_original_size += processed_original_size
                    
                    with open(processed_file, 'w') as f:
                        json.dump(result['processed_clusters'], f, indent=2, default=str)
                    
                    # Create ultra-lightweight version - NO large data objects
                    lightweight_processed = []
                    for processed_cluster in result['processed_clusters']:
                        # Extract timing logs for summary but save detailed timing separately
                        cluster_timing = processed_cluster.get('timing_logs', {})
                        timing_summary = {
                            'total_duration': cluster_timing.get('total_duration', 0),
                            'html_files_created': 0,
                            'site_similarity_duration': 0
                        }
                        
                        # Extract timing details
                        if cluster_timing.get('steps'):
                            timing_summary['html_files_created'] = cluster_timing['steps'].get('html_generation', {}).get('html_files_created', 0)
                            timing_summary['site_similarity_duration'] = cluster_timing['steps'].get('site_similarity_analysis', {}).get('duration', 0)
                        
                        lightweight_proc = {
                            'level': processed_cluster.get('level'),
                            'timing_summary': timing_summary,
                            'processed_data_file': f"large_data/{test_id}_processed_clusters.json",
                            # Keep summary info only
                            'summary': {
                                'has_sites_data': bool(processed_cluster.get('processed_data', {}).get('sites')),
                                'has_similarity_data': bool(processed_cluster.get('processed_data', {}).get('site_similarity')),
                                'sites_count': len(processed_cluster.get('processed_data', {}).get('sites', {})),
                                'html_files_count': len(processed_cluster.get('processed_data', {}).get('html_files', [])),
                                'similarity_total_sites': processed_cluster.get('processed_data', {}).get('site_similarity', {}).get('data', {}).get('summary', {}).get('total_sites', 0)
                            }
                        }
                        lightweight_processed.append(lightweight_proc)
                    
                    lightweight_result['processed_clusters'] = lightweight_processed
                    
                    # Calculate optimized size
                    processed_optimized_size = len(json.dumps(lightweight_processed, default=str).encode('utf-8'))
                    total_optimized_size += processed_optimized_size
                    
                    print(f"📁 Processed data: {processed_original_size/1024:.1f}KB → {processed_optimized_size/1024:.1f}KB")
                    
                except Exception as e:
                    print(f"❌ Failed to save processed data: {e}")
                    # Keep original data if saving fails
                    lightweight_result['processed_clusters'] = result.get('processed_clusters', [])
            
            # Save domain results with large data separately (for Mode 1)
            if 'domain_results' in result:
                domain_results_file = os.path.join(large_data_dir, f"{test_id}_domain_results.json")
                try:
                    # Calculate original size
                    domain_original_size = len(json.dumps(result['domain_results'], default=str).encode('utf-8'))
                    total_original_size += domain_original_size
                    
                    with open(domain_results_file, 'w') as f:
                        json.dump(result['domain_results'], f, indent=2, default=str)
                    
                    # Create ultra-lightweight version of domain results
                    lightweight_domains = []
                    for domain_result in result['domain_results']:
                        lightweight_domain = {
                            'domain': domain_result.get('domain'),
                            'urls': domain_result.get('urls'),
                            'status': domain_result.get('status'),
                            'message': domain_result.get('message'),
                            # Extract timing summary only
                            'timing_summary': {
                                'total_duration': domain_result.get('timing_logs', {}).get('total_duration', 0),
                                'cache_efficiency': domain_result.get('timing_logs', {}).get('performance_metrics', {}).get('cache_efficiency_percent', 0)
                            },
                            'summary': {
                                'html_files_count': len(domain_result.get('html_files', [])),
                                'clustering_results_count': len(domain_result.get('clustering_results', [])),
                                'processed_clusters_count': len(domain_result.get('processed_clusters', [])),
                                'successful_levels': len([cr for cr in domain_result.get('clustering_results', []) if cr.get('status') != 'error'])
                            },
                            'domain_data_file': f"large_data/{test_id}_domain_results.json"
                        }
                        lightweight_domains.append(lightweight_domain)
                    
                    lightweight_result['domain_results'] = lightweight_domains
                    
                    # Calculate optimized size
                    domain_optimized_size = len(json.dumps(lightweight_domains, default=str).encode('utf-8'))
                    total_optimized_size += domain_optimized_size
                    
                    print(f"📁 Domain data: {domain_original_size/1024:.1f}KB → {domain_optimized_size/1024:.1f}KB")
                    
                except Exception as e:
                    print(f"❌ Failed to save domain results data: {e}")
                    # Keep original data if saving fails
                    lightweight_result['domain_results'] = result.get('domain_results', [])
            
            # Keep only essential HTML files info
            if 'html_files' in result:
                html_files = result['html_files']
                lightweight_result['html_files_summary'] = {
                    'count': len(html_files),
                    'total_size_kb': sum(f.get('file_size_kb', 0) for f in html_files),
                    'levels': list(set(f.get('level') for f in html_files if f.get('level'))),
                    'domains': list(set(f.get('domain') for f in html_files if f.get('domain')))
                }
                # Save full HTML files list separately if it's large
                if len(html_files) > 10:
                    html_files_file = os.path.join(large_data_dir, f"{test_id}_html_files.json")
                    with open(html_files_file, 'w') as f:
                        json.dump(html_files, f, indent=2, default=str)
                    lightweight_result['html_files_summary']['full_list_file'] = f"large_data/{test_id}_html_files.json"
                else:
                    lightweight_result['html_files'] = html_files  # Keep small lists
            
            lightweight_results.append(lightweight_result)
        
        # Calculate overall optimization metrics
        if total_original_size > 0:
            optimization_ratio = ((total_original_size - total_optimized_size) / total_original_size) * 100
            print(f"\n📊 AGGRESSIVE OPTIMIZATION COMPLETE:")
            print(f"   💾 Original size: {total_original_size/1024:.1f} KB")
            print(f"   ⚡ Optimized size: {total_optimized_size/1024:.1f} KB")
            print(f"   🎯 Size reduction: {optimization_ratio:.1f}%")
        
        return lightweight_results 