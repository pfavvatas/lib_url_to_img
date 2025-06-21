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
        
        # Generate combinations ensuring fair mode distribution
        max_per_mode = rules['filters']['max_combinations_per_run'] // len(modes)
        
        for mode in modes:
            mode_test_count = 0
            for levels in level_combinations:
                for url_count in url_sizes:
                    if url_count <= len(available_urls):
                        # Create multiple random URL combinations for each parameter set
                        variations_limit = min(2, len(available_urls) // url_count)  # Reduced to 2 to fit more combinations
                        for variation in range(variations_limit):
                            # Skip if we've reached the limit for this mode
                            if mode_test_count >= max_per_mode:
                                break
                                
                            # Randomly select URLs
                            selected_urls = random.sample(available_urls, url_count)
                            
                            # Create test case
                            test_case = {
                                "id": f"test_{test_index:03d}_{mode}_L{'_'.join(map(str, levels if isinstance(levels, list) else [levels]))}_U{url_count}",
                                "name": f"Mode {mode} - Levels {levels} - {url_count} URLs",
                                "description": f"Testing Mode {mode} with levels {levels} using {url_count} randomly selected URLs",
                                "mode": mode,
                                "levels": levels if isinstance(levels, list) else [levels],
                                "urls": selected_urls,
                                "url_count": url_count,
                                "variation": variation + 1,
                                "estimated_duration": self.estimate_test_duration(url_count, levels),
                                "priority": self.calculate_priority(mode, levels, url_count)
                            }
                            test_cases.append(test_case)
                            test_index += 1
                            mode_test_count += 1
                        
                        # Break if mode limit reached
                        if mode_test_count >= max_per_mode:
                            break
                # Break if mode limit reached
                if mode_test_count >= max_per_mode:
                    break
        
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
            # Run the URL processing
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
        
        # Create experiment summary
        summary = {
            'experiment_info': {
                'name': experiment_name or 'Unnamed Experiment',
                'start_time': experiment_start_time,
                'end_time': experiment_end_time,
                'duration': experiment_duration,
                'total_tests': len(test_cases),
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': (successful_tests / len(test_cases)) * 100
            },
            'test_cases': test_cases,
            'results': results
        }
        
        # Save experiment summary
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
        """Generate data files for gnuplot charts"""
        gnuplot_dir = os.path.join(experiment_dir, "gnuplot_data")
        
        # Extract data for different chart types
        processing_times = []
        cluster_counts = []
        similarity_scores = []
        html_file_counts = []
        timing_analysis = []
        cache_efficiency = []
        step_timing = []
        
        for result in results:
            if result.get('status') == 'success':
                metadata = result.get('test_metadata', {})
                timing_logs = result.get('timing_logs', {})
                
                # Basic processing time data
                processing_times.append({
                    'test_id': metadata.get('test_id', ''),
                    'mode': metadata.get('mode', 0),
                    'levels': metadata.get('levels', []),
                    'url_count': metadata.get('url_count', 0),
                    'duration': metadata.get('duration', 0)
                })
                
                # Detailed timing analysis from timing logs
                if timing_logs.get('performance_metrics'):
                    perf = timing_logs['performance_metrics']
                    timing_analysis.append({
                        'test_id': metadata.get('test_id', ''),
                        'mode': metadata.get('mode', 0),
                        'url_count': metadata.get('url_count', 0),
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
                        'test_id': metadata.get('test_id', ''),
                        'mode': metadata.get('mode', 0),
                        'url_count': metadata.get('url_count', 0),
                        'cache_efficiency': perf.get('cache_efficiency_percent', 0),
                        'urls_from_cache': perf.get('urls_from_cache', 0),
                        'urls_newly_processed': perf.get('urls_newly_processed', 0),
                        'cache_savings': perf.get('cache_savings', 'N/A')
                    })
                
                # Step-by-step timing data
                if timing_logs.get('steps'):
                    for step_name, step_data in timing_logs['steps'].items():
                        step_timing.append({
                            'test_id': metadata.get('test_id', ''),
                            'mode': metadata.get('mode', 0),
                            'step_name': step_name,
                            'duration': step_data.get('duration', 0),
                            'description': step_data.get('description', ''),
                            'urls_processed': step_data.get('urls_processed', 0),
                            'cache_type': step_data.get('cache_type', 'none')
                        })
                
                # Cluster count data
                clustering_results = result.get('clustering_results', [])
                for cluster_result in clustering_results:
                    if cluster_result.get('cluster_info'):
                        cluster_counts.append({
                            'test_id': metadata.get('test_id', ''),
                            'mode': metadata.get('mode', 0),
                            'level': cluster_result.get('level', 0),
                            'cluster_count': cluster_result['cluster_info'].get('num_clusters', 0),
                            'dbcv_score': cluster_result['cluster_info'].get('dbcv_score', 0)
                        })
                
                # HTML files count
                html_files = result.get('html_files', [])
                html_file_counts.append({
                    'test_id': metadata.get('test_id', ''),
                    'mode': metadata.get('mode', 0),
                    'html_count': len(html_files)
                })
        
        # Save data files for gnuplot
        self.save_gnuplot_data_file(processing_times, os.path.join(gnuplot_dir, "processing_times.dat"))
        self.save_gnuplot_data_file(cluster_counts, os.path.join(gnuplot_dir, "cluster_counts.dat"))
        self.save_gnuplot_data_file(html_file_counts, os.path.join(gnuplot_dir, "html_file_counts.dat"))
        self.save_gnuplot_data_file(timing_analysis, os.path.join(gnuplot_dir, "timing_analysis.dat"))
        self.save_gnuplot_data_file(cache_efficiency, os.path.join(gnuplot_dir, "cache_efficiency.dat"))
        self.save_gnuplot_data_file(step_timing, os.path.join(gnuplot_dir, "step_timing.dat"))
        
        # Create gnuplot script template and execute them
        generated_images, execution_log = self.create_gnuplot_scripts(gnuplot_dir)
        return generated_images, execution_log
    
    def save_gnuplot_data_file(self, data: List[Dict], filename: str):
        """Save data in gnuplot-friendly format"""
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
    
    def create_gnuplot_scripts(self, gnuplot_dir: str):
        """Create sample gnuplot scripts for visualization and generate images"""
        
        # Create subdirectory for generated images
        images_dir = os.path.join(gnuplot_dir, "generated_images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Multiple output formats for thesis
        scripts_and_formats = [
            ("png", "png size 1200,800 font 'Arial,12'"),
            ("ps", "postscript enhanced color solid font 'Arial,12'"),
            ("eps", "postscript eps enhanced color solid font 'Arial,12'"),
            ("svg", "svg size 1200,800 font 'Arial,12'"),
            ("tex", "epslatex color solid")
        ]
        
        for format_ext, terminal_cmd in scripts_and_formats:
            # Processing time script
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
            
            # Cluster count script
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
            
            # Cache efficiency analysis script
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
            
            # Detailed timing analysis script
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
            
            # Performance comparison dashboard
            dashboard_script = f"""#!/usr/bin/gnuplot
set terminal {terminal_cmd}
set output 'generated_images/performance_dashboard.{format_ext}'
set multiplot layout 2,2 title 'Performance Analysis Dashboard - Thesis Data'

# Chart 1: Processing Time Comparison
set title 'Processing Time by Mode'
set xlabel 'URL Count'
set ylabel 'Time (seconds)'
set grid
plot 'processing_times.dat' using 4:($2==0?$5:1/0) with linespoints title 'Mode 0' pt 7 lc rgb 'blue', \\
     'processing_times.dat' using 4:($2==1?$5:1/0) with linespoints title 'Mode 1' pt 5 lc rgb 'red'

# Chart 2: Cache Efficiency
set title 'Cache Efficiency'
set xlabel 'URL Count'
set ylabel 'Efficiency (%)'
set yrange [0:100]
plot 'cache_efficiency.dat' using 3:4 with linespoints title 'Cache Hit Rate' pt 9 lc rgb 'green'

# Chart 3: Clustering Quality
set title 'Clustering Results'
set xlabel 'DOM Level'
set ylabel 'Cluster Count'
set yrange [0:*]
plot 'cluster_counts.dat' using 3:4 with linespoints title 'Clusters Generated' pt 7 lc rgb 'purple'

# Chart 4: HTML Output
set title 'HTML Files Generated'
set xlabel 'Test Case'
set ylabel 'File Count'
plot 'html_file_counts.dat' using 0:3 with impulses title 'HTML Files' lc rgb 'orange'

unset multiplot
"""
            
            with open(os.path.join(gnuplot_dir, f"performance_dashboard_{format_ext}.gnuplot"), 'w') as f:
                f.write(dashboard_script)
        
        # Try to execute gnuplot and generate images automatically
        generated_images, execution_log = self.execute_gnuplot_scripts(gnuplot_dir)
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
            
            # Find all gnuplot scripts
            gnuplot_scripts = glob.glob("*.gnuplot")
            execution_log.append(f"Found {len(gnuplot_scripts)} gnuplot scripts")
            print(f"📊 Found {len(gnuplot_scripts)} gnuplot scripts to execute")
            
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