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
            
            # Add test metadata to result
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
        
        for result in results:
            if result.get('status') == 'success':
                metadata = result.get('test_metadata', {})
                
                # Processing time data
                processing_times.append({
                    'test_id': metadata.get('test_id', ''),
                    'mode': metadata.get('mode', 0),
                    'levels': metadata.get('levels', []),
                    'url_count': metadata.get('url_count', 0),
                    'duration': metadata.get('duration', 0)
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
                
                # Try to install gnuplot
                try:
                    install_result = subprocess.run(['sudo', 'apt', 'update', '&&', 'sudo', 'apt', 'install', '-y', 'gnuplot'], 
                                                  shell=True,
                                                  capture_output=True, 
                                                  text=True, 
                                                  timeout=300)
                    
                    if install_result.returncode == 0:
                        print("✅ Gnuplot installed successfully!")
                        execution_log.append("Gnuplot installed successfully!")
                    else:
                        print("⚠️ Failed to install gnuplot automatically")
                        execution_log.append("Failed to install gnuplot automatically")
                        print("📝 Manual installation: sudo apt install gnuplot")
                        execution_log.append("Manual installation required: sudo apt install gnuplot")
                        return generated_images, execution_log
                except Exception as e:
                    print(f"⚠️ Error installing gnuplot: {e}")
                    execution_log.append(f"Error installing gnuplot: {e}")
                    return generated_images, execution_log
            
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
                        print(f"✅ Successfully generated images from {script}")
                        execution_log.append(f"Successfully generated images from {script}")
                        
                        # Check what images were generated
                        images_dir = os.path.join(gnuplot_dir, "generated_images")
                        if os.path.exists(images_dir):
                            for image_file in os.listdir(images_dir):
                                if image_file.endswith(('.png', '.ps', '.eps', '.svg', '.tex')):
                                    file_size = os.path.getsize(os.path.join(images_dir, image_file))
                                    generated_images.append({
                                        'filename': image_file,
                                        'script': script,
                                        'path': os.path.join("generated_images", image_file),
                                        'size_bytes': file_size,
                                        'size_kb': file_size / 1024,
                                        'format': image_file.split('.')[-1].upper()
                                    })
                    else:
                        error_msg = f"Gnuplot script {script} failed: {result.stderr}"
                        print(f"❌ {error_msg}")
                        execution_log.append(error_msg)
                        
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