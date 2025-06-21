import os
import webbrowser
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from flasgger import Swagger
import sys

# Add the lib directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from lib import process_urls_from_api, process_clusters_from_api
from utils.cache_manager import CacheManager

# Import experiment manager with error handling
try:
    from experiment_manager import ExperimentManager
    experiment_manager_available = True
    print("✅ ExperimentManager imported successfully")
except Exception as e:
    print(f"❌ Failed to import ExperimentManager: {e}")
    experiment_manager_available = False
    ExperimentManager = None

app = Flask(__name__)
# Configure CORS more specifically
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization"]
    }
})

# Enable Swagger only if the environment variable is set
enable_swagger = os.getenv('ENABLE_SWAGGER', 'true').lower() in ['true', '1', 'yes']
swagger = Swagger(app) if enable_swagger else None  # Initialize Swagger if enabled

# Get absolute path to output_html_files directory
OUTPUT_HTML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'output_html_files'))

# HTML template for file not found error
FILE_NOT_FOUND_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>File Not Found</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .error-container {
            background-color: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
            width: 90%;
        }
        h1 {
            color: #e74c3c;
            margin-bottom: 1rem;
        }
        p {
            color: #666;
            margin-bottom: 1.5rem;
        }
        .file-name {
            background-color: #f8f9fa;
            padding: 0.5rem;
            border-radius: 4px;
            font-family: monospace;
            margin: 1rem 0;
        }
        .back-button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .back-button:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>File Not Found</h1>
        <p>The requested file could not be found on the server.</p>
        <div class="file-name">{{ filename }}</div>
        <p>This file may have been deleted or never existed.</p>
        <a href="javascript:history.back()" class="back-button">Go Back</a>
    </div>
</body>
</html>
"""

@app.route('/output_html_files/<path:filename>')
def serve_html(filename):
    try:
        # Ensure the directory exists
        if not os.path.exists(OUTPUT_HTML_DIR):
            os.makedirs(OUTPUT_HTML_DIR)
            print(f"Created directory: {OUTPUT_HTML_DIR}")
        
        # Handle level-based directory structure (e.g., level_1/filename.html)
        file_path = os.path.join(OUTPUT_HTML_DIR, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            # Return HTML error page instead of JSON
            return render_template_string(FILE_NOT_FOUND_TEMPLATE, filename=filename), 404
            
        print(f"Serving file: {file_path}")
        # Use the directory containing the file for send_from_directory
        directory = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        return send_from_directory(directory, basename)
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return render_template_string(FILE_NOT_FOUND_TEMPLATE, filename=filename), 500

@app.route('/site-similarity', methods=['POST'])
def site_similarity():
    """
    Compute site similarity analysis
    ---
    tags:
      - Site Analysis
    parameters:
      - name: sites
        in: body
        required: true
        schema:
          type: object
          properties:
            sites:
              type: object
              description: Dictionary with site URLs as keys and cluster ID arrays as values
              example: {"site1.com": [1, 2, 3], "site2.com": [1, 3, 2]}
    responses:
      200:
        description: Site similarity analysis results
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
            data:
              type: object
    """
    try:
        data = request.json
        sites_data = data.get('sites', {})
        
        if not sites_data:
            return jsonify({
                "status": "error",
                "message": "Sites data is required",
                "data": None
            }), 400
        
        # Import here to avoid circular imports
        sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
        from utils.site_similarity import compute_site_cosine_similarity
        
        result = compute_site_cosine_similarity(sites_data)
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error in site similarity analysis: {str(e)}",
            "data": None,
            "traceback": traceback.format_exc()
        }), 500

@app.route('/site-similarity', methods=['OPTIONS'])
def site_similarity_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/process-urls', methods=['POST'])
def process_urls():
    """
    Process a list of URLs
    ---
    tags:
      - URL Processing
    parameters:
      - name: urls
        in: body
        required: true
        schema:
          type: object
          properties:
            urls:
              type: array
              items:
                type: string
              example: ["http://example.com", "http://test.com"]
            levels:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
            mode:
              type: integer
              description: Processing mode (0 for all URLs together, 1 for domain-based processing)
              example: 0
    responses:
      200:
        description: A list of processed results
        schema:
          type: object
          additionalProperties:
            type: string
    """
    data = request.json
    urls = data.get('urls', [])
    levels = data.get('levels', [])
    mode = data.get('mode', 0)  # Default to mode 0 if not specified
    results = process_urls_from_api(urls, levels, mode)
    response = jsonify(results)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/process-urls', methods=['OPTIONS'])
def process_urls_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/process-clusters', methods=['POST'])
def process_clusters():
    """
    Process cluster data
    ---
    tags:
      - Cluster Processing
    parameters:
      - name: clusters
        in: body
        required: true
        schema:
          type: object
          properties:
            clusters:
              type: string
              example: "cluster data here"
    responses:
      200:
        description: Processed cluster results
        schema:
          type: object
          additionalProperties:
            type: string
    """
    data = request.json
    clusters_data = data.get('clusters', '')
    # Process the clusters data
    results = process_clusters_from_api(clusters_data)
    response = jsonify(results)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/process-clusters', methods=['OPTIONS'])
def process_clusters_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Initialize cache manager and experiment manager
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cache_manager = CacheManager(cache_dir=os.path.join(PROJECT_ROOT, "backend", "api", "cache"))

# Initialize experiment manager if available
experiment_manager = None
if experiment_manager_available and ExperimentManager:
    try:
        experiment_manager = ExperimentManager()
        print("✅ ExperimentManager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ExperimentManager: {e}")
        experiment_manager_available = False

@app.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """
    Get cache statistics
    ---
    tags:
      - Cache Management
    responses:
      200:
        description: Cache statistics
        schema:
          type: object
          properties:
            status:
              type: string
            data:
              type: object
    """
    try:
        stats = cache_manager.get_cache_stats()
        
        response = jsonify({
            "status": "success",
            "data": stats
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error getting cache stats: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/cache/entries', methods=['GET'])
def list_cache_entries():
    """
    List all cache entries
    ---
    tags:
      - Cache Management
    responses:
      200:
        description: List of cache entries
        schema:
          type: object
          properties:
            status:
              type: string
            data:
              type: array
    """
    try:
        entries = cache_manager.list_cache_entries()
        
        response = jsonify({
            "status": "success",
            "data": entries
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error listing cache entries: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """
    Clean up expired cache entries
    ---
    tags:
      - Cache Management
    parameters:
      - name: ttl_hours
        in: body
        required: false
        schema:
          type: object
          properties:
            ttl_hours:
              type: integer
              description: TTL in hours (optional, uses default if not provided)
    responses:
      200:
        description: Cleanup results
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
            removed_count:
              type: integer
    """
    try:
        data = request.json or {}
        ttl_hours = data.get('ttl_hours')
        
        removed_count = cache_manager.cleanup_expired(ttl_hours)
        
        response = jsonify({
            "status": "success",
            "message": f"Cleanup completed",
            "removed_count": removed_count
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error during cache cleanup: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    Clear all cache entries
    ---
    tags:
      - Cache Management
    responses:
      200:
        description: Clear cache results
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
            removed_count:
              type: integer
    """
    try:
        removed_count = cache_manager.clear_all_cache()
        
        response = jsonify({
            "status": "success",
            "message": f"All cache cleared",
            "removed_count": removed_count
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error clearing cache: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/cache/check', methods=['POST'])
def check_cache():
    """
    Check if cache exists for specific URLs and levels
    ---
    tags:
      - Cache Management
    parameters:
      - name: request_data
        in: body
        required: true
        schema:
          type: object
          properties:
            urls:
              type: array
              items:
                type: string
            levels:
              type: array
              items:
                type: integer
            ttl_hours:
              type: integer
              description: Custom TTL in hours (optional)
    responses:
      200:
        description: Cache check results
        schema:
          type: object
          properties:
            status:
              type: string
            has_cache:
              type: boolean
            cache_key:
              type: string
    """
    try:
        data = request.json
        urls = data.get('urls', [])
        levels = data.get('levels', [])
        ttl_hours = data.get('ttl_hours')
        
        has_cache, cache_key = cache_manager.has_valid_cache(urls, levels, ttl_hours)
        
        response = jsonify({
            "status": "success",
            "has_cache": has_cache,
            "cache_key": cache_key[:8] + "..." if cache_key else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error checking cache: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

# OPTIONS endpoints for cache management
@app.route('/cache/<path:endpoint>', methods=['OPTIONS'])
def cache_options(endpoint):
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# EXPERIMENT MANAGEMENT ENDPOINTS

@app.route('/experiments/test', methods=['GET'])
def test_experiments():
    """
    Test experiment endpoints
    ---
    tags:
      - Experiment Management
    responses:
      200:
        description: Test response
    """
    response = jsonify({
        "status": "success",
        "message": "Experiment endpoints are working",
        "experiment_manager_available": experiment_manager_available,
        "experiment_manager_initialized": experiment_manager is not None
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/experiments/test-cases', methods=['GET'])
def get_test_cases():
    """
    Get all available test case combinations
    ---
    tags:
      - Experiment Management
    responses:
      200:
        description: List of available test cases
        schema:
          type: object
          properties:
            status:
              type: string
            test_cases:
              type: array
            total_count:
              type: integer
    """
    if not experiment_manager_available or not experiment_manager:
        return jsonify({
            "status": "error",
            "message": "Experiment manager is not available. Check server logs for import errors."
        }), 500
        
    try:
        test_cases = experiment_manager.get_available_test_cases()
        
        response = jsonify({
            "status": "success",
            "test_cases": test_cases,
            "total_count": len(test_cases)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error getting test cases: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/filter-test-cases', methods=['POST'])
def filter_test_cases():
    """
    Filter test cases based on criteria
    ---
    tags:
      - Experiment Management
    parameters:
      - name: filters
        in: body
        required: true
        schema:
          type: object
          properties:
            priority:
              type: array
              items:
                type: string
              example: ["high", "medium"]
            max_duration:
              type: number
              example: 10.0
            modes:
              type: array
              items:
                type: integer
              example: [0, 1]
            max_url_count:
              type: integer
              example: 5
    responses:
      200:
        description: Filtered test cases
        schema:
          type: object
          properties:
            status:
              type: string
            test_cases:
              type: array
            total_count:
              type: integer
    """
    if not experiment_manager_available or not experiment_manager:
        return jsonify({
            "status": "error",
            "message": "Experiment manager is not available. Check server logs for import errors."
        }), 500
        
    try:
        data = request.json
        filters = data.get('filters', {})
        
        all_test_cases = experiment_manager.get_available_test_cases()
        filtered_test_cases = experiment_manager.filter_test_cases(all_test_cases, filters)
        
        response = jsonify({
            "status": "success",
            "test_cases": filtered_test_cases,
            "total_count": len(filtered_test_cases),
            "original_count": len(all_test_cases)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error filtering test cases: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/run-batch', methods=['POST'])
def run_experiment_batch():
    """
    Run a batch of experiment test cases
    ---
    tags:
      - Experiment Management
    parameters:
      - name: experiment_data
        in: body
        required: true
        schema:
          type: object
          properties:
            experiment_name:
              type: string
              example: "thesis_experiment_1"
            test_case_ids:
              type: array
              items:
                type: string
              example: ["test_001_0_L1_U3", "test_002_1_L2_U4"]
            selected_test_cases:
              type: array
              description: "Alternative to test_case_ids - full test case objects"
    responses:
      200:
        description: Experiment batch execution results
        schema:
          type: object
          properties:
            status:
              type: string
            experiment_summary:
              type: object
    """
    if not experiment_manager_available or not experiment_manager:
        return jsonify({
            "status": "error",
            "message": "Experiment manager is not available. Check server logs for import errors."
        }), 500
        
    try:
        data = request.json
        experiment_name = data.get('experiment_name', 'Unnamed Experiment')
        
        # Get test cases either by IDs or directly provided
        if 'selected_test_cases' in data:
            test_cases = data['selected_test_cases']
        elif 'test_case_ids' in data:
            all_test_cases = experiment_manager.get_available_test_cases()
            test_case_ids = data['test_case_ids']
            test_cases = [tc for tc in all_test_cases if tc['id'] in test_case_ids]
        else:
            return jsonify({
                "status": "error",
                "message": "Either 'selected_test_cases' or 'test_case_ids' must be provided"
            }), 400
        
        if not test_cases:
            return jsonify({
                "status": "error",
                "message": "No valid test cases found to run"
            }), 400
        
        # Run the experiment batch
        experiment_summary = experiment_manager.run_experiment_batch(test_cases, experiment_name)
        
        response = jsonify({
            "status": "success",
            "experiment_summary": experiment_summary
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error running experiment batch: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/config', methods=['GET'])
def get_experiment_config():
    """
    Get the experiment configuration
    ---
    tags:
      - Experiment Management
    responses:
      200:
        description: Experiment configuration
        schema:
          type: object
          properties:
            status:
              type: string
            config:
              type: object
    """
    if not experiment_manager_available or not experiment_manager:
        return jsonify({
            "status": "error",
            "message": "Experiment manager is not available. Check server logs for import errors."
        }), 500
        
    try:
        config = experiment_manager.config
        
        response = jsonify({
            "status": "success",
            "config": config
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error getting experiment config: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/results/list', methods=['GET'])
def list_experiment_results():
    """
    List all available experiment results
    ---
    tags:
      - Experiment Management
    responses:
      200:
        description: List of experiment results
        schema:
          type: object
          properties:
            status:
              type: string
            experiments:
              type: array
    """
    try:
        import glob
        import json
        from datetime import datetime
        
        # Look for experiment directories
        results_pattern = os.path.join("experiment_results", "*_*")
        experiment_dirs = glob.glob(results_pattern)
        
        experiments = []
        for exp_dir in experiment_dirs:
            summary_file = os.path.join(exp_dir, "experiment_summary.json")
            if os.path.exists(summary_file):
                try:
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                    
                    # Extract metadata
                    experiment_info = summary.get('experiment_info', {})
                    exp_name = experiment_info.get('name', 'Unknown')
                    
                    # Parse timestamp from directory name
                    dir_name = os.path.basename(exp_dir)
                    timestamp_part = dir_name.split('_')[0] + '_' + dir_name.split('_')[1] + '_' + dir_name.split('_')[2]
                    
                    experiments.append({
                        'id': dir_name,
                        'name': exp_name,
                        'timestamp': timestamp_part,
                        'directory': exp_dir,
                        'total_tests': experiment_info.get('total_tests', 0),
                        'successful_tests': experiment_info.get('successful_tests', 0),
                        'failed_tests': experiment_info.get('failed_tests', 0),
                        'success_rate': experiment_info.get('success_rate', 0),
                        'duration': experiment_info.get('duration', 0),
                        'start_time': experiment_info.get('start_time', 0),
                        'end_time': experiment_info.get('end_time', 0)
                    })
                except Exception as e:
                    print(f"Error reading summary for {exp_dir}: {e}")
                    continue
        
        # Sort by timestamp (most recent first)
        experiments.sort(key=lambda x: x['start_time'], reverse=True)
        
        response = jsonify({
            "status": "success",
            "experiments": experiments,
            "total_count": len(experiments)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error listing experiment results: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/results/<experiment_id>', methods=['GET'])
def get_experiment_result(experiment_id):
    """
    Get detailed results for a specific experiment
    ---
    tags:
      - Experiment Management
    parameters:
      - name: experiment_id
        in: path
        type: string
        required: true
        description: The experiment directory name
    responses:
      200:
        description: Detailed experiment results
        schema:
          type: object
          properties:
            status:
              type: string
            experiment_data:
              type: object
    """
    try:
        import json
        
        # Construct the path to the experiment directory
        exp_dir = os.path.join("experiment_results", experiment_id)
        summary_file = os.path.join(exp_dir, "experiment_summary.json")
        
        if not os.path.exists(summary_file):
            return jsonify({
                "status": "error",
                "message": f"Experiment {experiment_id} not found"
            }), 404
        
        # Load the complete experiment summary
        with open(summary_file, 'r') as f:
            experiment_data = json.load(f)
        
        # Add additional metadata
        experiment_data['id'] = experiment_id
        experiment_data['directory'] = exp_dir
        
        # Check for gnuplot data files and generated images
        gnuplot_dir = os.path.join(exp_dir, "gnuplot_data")
        gnuplot_files = []
        generated_images = []
        
        if os.path.exists(gnuplot_dir):
            # Scan main directory for data and script files
            for file in os.listdir(gnuplot_dir):
                if file.endswith(('.dat', '.gnuplot')):
                    file_path = os.path.join(gnuplot_dir, file)
                    file_size = os.path.getsize(file_path)
                    gnuplot_files.append({
                        'filename': file,
                        'path': file_path,
                        'size_bytes': file_size,
                        'size_kb': file_size / 1024,
                        'type': 'data' if file.endswith('.dat') else 'script'
                    })
            
            # Scan for generated images
            images_dir = os.path.join(gnuplot_dir, "generated_images")
            if os.path.exists(images_dir):
                for file in os.listdir(images_dir):
                    if file.endswith(('.png', '.ps', '.eps', '.svg', '.tex')):
                        file_path = os.path.join(images_dir, file)
                        file_size = os.path.getsize(file_path)
                        generated_images.append({
                            'filename': file,
                            'path': file_path,
                            'relative_path': f"gnuplot_data/generated_images/{file}",
                            'size_bytes': file_size,
                            'size_kb': file_size / 1024,
                            'format': file.split('.')[-1].upper(),
                            'chart_type': file.split('.')[0].replace('_', ' ').title()
                        })
        
        experiment_data['gnuplot_files'] = gnuplot_files
        experiment_data['generated_images'] = generated_images
        
        response = jsonify({
            "status": "success",
            "experiment_data": experiment_data
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error loading experiment {experiment_id}: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/results/<experiment_id>/files/<filename>', methods=['GET'])
def download_experiment_file(experiment_id, filename):
    """
    Download a specific file from an experiment (gnuplot data or script)
    ---
    tags:
      - Experiment Management
    parameters:
      - name: experiment_id
        in: path
        type: string
        required: true
        description: The experiment directory name
      - name: filename
        in: path
        type: string
        required: true
        description: The filename to download
    responses:
      200:
        description: File content
      404:
        description: File not found
    """
    try:
        import os
        
        # Construct the path to the file
        exp_dir = os.path.join("experiment_results", experiment_id)
        gnuplot_dir = os.path.join(exp_dir, "gnuplot_data")
        file_path = os.path.join(gnuplot_dir, filename)
        
        # Security check - ensure the file is within the expected directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(gnuplot_dir)):
            return jsonify({
                "status": "error",
                "message": "Invalid file path"
            }), 400
        
        if not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": f"File {filename} not found in experiment {experiment_id}"
            }), 404
        
        # Determine content type based on file extension
        content_type = 'text/plain'
        if filename.endswith('.dat'):
            content_type = 'text/tab-separated-values'
        elif filename.endswith('.gnuplot'):
            content_type = 'text/plain'
        
        # Send the file
        return send_from_directory(
            gnuplot_dir, 
            filename, 
            as_attachment=True,
            download_name=filename,
            mimetype=content_type
        )
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error downloading file: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/results/<experiment_id>/files/<filename>/content', methods=['GET'])
def get_experiment_file_content(experiment_id, filename):
    """
    Get the content of a specific file from an experiment for preview/copy
    ---
    tags:
      - Experiment Management
    parameters:
      - name: experiment_id
        in: path
        type: string
        required: true
        description: The experiment directory name
      - name: filename
        in: path
        type: string
        required: true
        description: The filename to read
    responses:
      200:
        description: File content as JSON
        schema:
          type: object
          properties:
            status:
              type: string
            content:
              type: string
            filename:
              type: string
            size:
              type: integer
    """
    try:
        import os
        
        # Construct the path to the file
        exp_dir = os.path.join("experiment_results", experiment_id)
        gnuplot_dir = os.path.join(exp_dir, "gnuplot_data")
        file_path = os.path.join(gnuplot_dir, filename)
        
        # Security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(gnuplot_dir)):
            return jsonify({
                "status": "error",
                "message": "Invalid file path"
            }), 400
        
        if not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": f"File {filename} not found"
            }), 404
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_size = os.path.getsize(file_path)
        
        response = jsonify({
            "status": "success",
            "content": content,
            "filename": filename,
            "size": file_size,
            "type": "data" if filename.endswith('.dat') else "script"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error reading file: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/results/<experiment_id>/images/<filename>', methods=['GET'])
def serve_experiment_image(experiment_id, filename):
    """
    Serve generated images from experiment results
    ---
    tags:
      - Experiment Management  
    parameters:
      - name: experiment_id
        in: path
        type: string
        required: true
        description: The experiment directory name
      - name: filename
        in: path
        type: string
        required: true
        description: The image filename
    responses:
      200:
        description: Image file
      404:
        description: Image not found
    """
    try:
        import os
        
        # Construct the path to the image
        exp_dir = os.path.join("experiment_results", experiment_id)
        images_dir = os.path.join(exp_dir, "gnuplot_data", "generated_images")
        file_path = os.path.join(images_dir, filename)
        
        # Security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(images_dir)):
            return jsonify({
                "status": "error",
                "message": "Invalid file path"
            }), 400
        
        if not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": f"Image {filename} not found"
            }), 404
        
        # Determine content type based on file extension
        content_types = {
            '.png': 'image/png',
            '.ps': 'application/postscript',
            '.eps': 'application/postscript',
            '.svg': 'image/svg+xml',
            '.tex': 'text/plain'
        }
        
        file_ext = '.' + filename.split('.')[-1].lower()
        content_type = content_types.get(file_ext, 'application/octet-stream')
        
        # Send the file
        return send_from_directory(
            images_dir, 
            filename, 
            mimetype=content_type
        )
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error serving image: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/gnuplot-guide', methods=['GET'])
def get_gnuplot_guide():
    """
    Get gnuplot visualization guide and sample scripts
    ---
    tags:
      - Experiment Management
    responses:
      200:
        description: Gnuplot guide and sample scripts
        schema:
          type: object
          properties:
            status:
              type: string
            guide:
              type: object
    """
    guide = {
        "setup": {
            "installation": {
                "ubuntu": "sudo apt-get install gnuplot",
                "windows": "Download from http://www.gnuplot.info/download.html",
                "mac": "brew install gnuplot"
            },
            "basic_usage": "gnuplot script.gnuplot",
            "interactive_mode": "gnuplot -persist -e \"plot 'data.dat' with lines\""
        },
        "data_files_structure": {
            "processing_times.dat": {
                "columns": ["test_id", "mode", "levels", "url_count", "duration"],
                "description": "Processing time data for each test case",
                "sample_data": "test_001\t0\t[1,2]\t3\t12.45"
            },
            "cluster_counts.dat": {
                "columns": ["test_id", "mode", "level", "cluster_count", "dbcv_score"],
                "description": "Number of clusters generated per level",
                "sample_data": "test_001\t0\t1\t5\t0.567"
            },
            "html_file_counts.dat": {
                "columns": ["test_id", "mode", "html_count"],
                "description": "Number of HTML files generated per test",
                "sample_data": "test_001\t0\t15"
            }
        },
        "sample_scripts": {
            "processing_time_comparison": """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'processing_time_comparison.png'
set title 'Web Scraping Processing Time: Mode 0 vs Mode 1\\nData: Total processing time (seconds) for URL clustering analysis'
set xlabel 'Number of URLs Processed'
set ylabel 'Processing Time (seconds)'
set grid
set key top left
set style data points
set pointsize 1.5

# Filter data by mode and plot
plot 'processing_times.dat' using 4:($2==0?$5:1/0) with linespoints title 'Mode 0 (All Together)' pt 7 lc rgb 'blue', \\
     'processing_times.dat' using 4:($2==1?$5:1/0) with linespoints title 'Mode 1 (Domain-based)' pt 5 lc rgb 'red'
""",
            "clustering_quality_by_level": """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'clustering_quality_by_level.png'
set title 'HDBSCAN Clustering Quality (DBCV Score) by DOM Level\\nData: Density-Based Clustering Validation scores (-1 to 1 scale)'
set xlabel 'DOM Tree Level'
set ylabel 'DBCV Score (Clustering Quality)'
set grid
set key top right
set xrange [0.5:5.5]
set yrange [-0.5:1]

plot 'cluster_counts.dat' using 3:($2==0?$5:1/0) with linespoints title 'Mode 0' pt 7 lc rgb 'blue', \\
     'cluster_counts.dat' using 3:($2==1?$5:1/0) with linespoints title 'Mode 1' pt 5 lc rgb 'red'
""",
            "clusters_vs_urls": """#!/usr/bin/gnuplot
set terminal png size 1200,800 font 'Arial,12'
set output 'clusters_vs_urls.png'
set title 'Number of Clusters Generated vs URL Count\\nData: Cluster formation patterns across different input sizes'
set xlabel 'Number of URLs in Test'
set ylabel 'Average Number of Clusters Generated'
set grid
set key top left

# Create temporary aggregated data
set table 'temp_mode0.dat'
plot 'processing_times.dat' using 4:($2==0?1:0) smooth frequency
unset table

set table 'temp_mode1.dat'
plot 'processing_times.dat' using 4:($2==1?1:0) smooth frequency
unset table

plot 'temp_mode0.dat' using 1:2 with linespoints title 'Mode 0' pt 7 lc rgb 'blue', \\
     'temp_mode1.dat' using 1:2 with linespoints title 'Mode 1' pt 5 lc rgb 'red'

# Clean up temporary files
system("rm -f temp_mode0.dat temp_mode1.dat")
""",
            "performance_heatmap": """#!/usr/bin/gnuplot
set terminal png size 1000,800 font 'Arial,12'
set output 'performance_heatmap.png'
set title 'Performance Heatmap: Processing Time by Mode and URL Count'
set xlabel 'Number of URLs'
set ylabel 'Processing Mode'
set zlabel 'Processing Time (seconds)'
set pm3d map
set palette rgb 33,13,10
set cbrange [0:*]

# Convert processing times to grid format
splot 'processing_times.dat' using 4:2:5 with pm3d
"""
        },
        "thesis_analysis_tips": {
            "comparative_analysis": [
                "Compare Mode 0 vs Mode 1 processing times across different URL counts",
                "Analyze clustering quality (DBCV scores) between modes",
                "Study the relationship between DOM levels and clustering effectiveness",
                "Examine scalability patterns as input size increases"
            ],
            "statistical_analysis": [
                "Calculate mean, median, and standard deviation for processing times",
                "Perform t-tests to compare mode performance statistically",
                "Analyze correlation between URL count and processing time",
                "Study clustering consistency across multiple runs"
            ],
            "visualization_recommendations": [
                "Use box plots to show processing time distributions",
                "Create scatter plots with trend lines for scalability analysis",
                "Generate heatmaps for multi-dimensional comparisons",
                "Include error bars to show variance in measurements"
            ]
        },
        "advanced_scripts": {
            "box_plot_comparison": """#!/usr/bin/gnuplot
set terminal png size 1200,600 font 'Arial,12'
set output 'processing_time_boxplot.png'
set title 'Processing Time Distribution Comparison\\nData: Statistical distribution of processing times by mode'
set ylabel 'Processing Time (seconds)'
set xlabel 'Processing Mode'
set grid ytics
set style boxplot outliers pointtype 7
set style data boxplot
set style fill solid 0.5 border -1
set xtics ('Mode 0' 0, 'Mode 1' 1)

plot 'processing_times.dat' using (($2==0)?0:1/0):5 title 'Mode 0', \\
     'processing_times.dat' using (($2==1)?1:1/0):5 title 'Mode 1'
""",
            "multi_chart_dashboard": """#!/usr/bin/gnuplot
set terminal png size 1600,1200 font 'Arial,10'
set output 'thesis_dashboard.png'
set multiplot layout 2,2 title 'Thesis Analysis Dashboard - Web Scraping Performance Study'

# Chart 1: Processing Time
set title 'Processing Time Comparison'
set xlabel 'URL Count'
set ylabel 'Time (seconds)'
plot 'processing_times.dat' using 4:($2==0?$5:1/0) with lines title 'Mode 0', \\
     'processing_times.dat' using 4:($2==1?$5:1/0) with lines title 'Mode 1'

# Chart 2: Clustering Quality
set title 'Clustering Quality (DBCV Score)'
set xlabel 'DOM Level'
set ylabel 'DBCV Score'
plot 'cluster_counts.dat' using 3:($2==0?$5:1/0) with points title 'Mode 0', \\
     'cluster_counts.dat' using 3:($2==1?$5:1/0) with points title 'Mode 1'

# Chart 3: Cluster Count
set title 'Number of Clusters Generated'
set xlabel 'DOM Level'
set ylabel 'Cluster Count'
plot 'cluster_counts.dat' using 3:($2==0?$4:1/0) with lines title 'Mode 0', \\
     'cluster_counts.dat' using 3:($2==1?$4:1/0) with lines title 'Mode 1'

# Chart 4: HTML Output
set title 'HTML Files Generated'
set xlabel 'Test Case'
set ylabel 'File Count'
plot 'html_file_counts.dat' using 0:($2==0?$3:1/0) with impulses title 'Mode 0', \\
     'html_file_counts.dat' using 0:($2==1?$3:1/0) with impulses title 'Mode 1'

unset multiplot
"""
        }
    }
    
    response = jsonify({
        "status": "success",
        "guide": guide
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# OPTIONS endpoints for experiment management
@app.route('/experiments/<path:endpoint>', methods=['OPTIONS'])
def experiments_options(endpoint):
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def run_price_processes(urls):
    # Dummy implementation, replace with your existing processing logic
    return {url: f"Processed data for {url}" for url in urls}

def open_browser():
    port = int(os.getenv('PORT', 5000))
    webbrowser.open(f'http://localhost:{port}/apidocs')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() in ['true', '1', 'yes']
    use_reloader = os.getenv('FLASK_USE_RELOADER', 'false').lower() in ['true', '1', 'yes']
    
    open_browser()
    app.run(
        debug=debug_mode, 
        host='0.0.0.0', 
        port=port, 
        use_reloader=use_reloader, 
        threaded=True
    )