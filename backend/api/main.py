import os
import webbrowser
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from flasgger import Swagger
import sys
import json

# Add the lib directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from lib import process_urls_from_api, process_clusters_from_api


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
# HTML files are created relative to the project root, not the API directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_HTML_DIR = os.path.join(PROJECT_ROOT, "output_html_files")
print(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
print(f"📁 OUTPUT_HTML_DIR: {OUTPUT_HTML_DIR}")
print(f"📁 OUTPUT_HTML_DIR exists: {os.path.exists(OUTPUT_HTML_DIR)}")

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
        print(f"🔍 Attempting to serve file: {file_path}")
        print(f"📁 Full path: {os.path.abspath(file_path)}")
        print(f"✅ File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            # List available files in the directory for debugging
            try:
                dir_to_check = os.path.dirname(file_path) if os.path.dirname(file_path) else OUTPUT_HTML_DIR
                if os.path.exists(dir_to_check):
                    available_files = os.listdir(dir_to_check)
                    print(f"📋 Available files in {dir_to_check}: {available_files[:10]}")  # Show first 10 files
                else:
                    print(f"📁 Directory doesn't exist: {dir_to_check}")
            except Exception as debug_e:
                print(f"🐛 Debug error: {debug_e}")
            
            return render_template_string(FILE_NOT_FOUND_TEMPLATE, filename=filename), 404
            
        print(f"✅ Serving file: {file_path}")
        
        # Fix the directory path issue - use absolute paths
        abs_file_path = os.path.abspath(file_path)
        directory = os.path.dirname(abs_file_path)
        basename = os.path.basename(abs_file_path)
        
        print(f"📂 Serving from directory: {directory}")
        print(f"📄 File basename: {basename}")
        
        return send_from_directory(directory, basename)
    except Exception as e:
        print(f"❌ Error serving file: {str(e)}")
        import traceback
        print(f"🐛 Stack trace: {traceback.format_exc()}")
        return render_template_string(FILE_NOT_FOUND_TEMPLATE, filename=filename), 500

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

# Initialize experiment manager if available
experiment_manager = None
if experiment_manager_available and ExperimentManager:
    try:
        experiment_manager = ExperimentManager()
        print("✅ ExperimentManager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ExperimentManager: {e}")
        experiment_manager_available = False

# EXPERIMENT MANAGEMENT ENDPOINTS



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
        
        # Extract gnuplot data for frontend compatibility
        gnuplot_files = []
        generated_images = []
        experiment_id = None
        
        # Get experiment ID from the directory name
        if hasattr(experiment_manager, 'current_experiment_dir') and experiment_manager.current_experiment_dir:
            experiment_id = os.path.basename(experiment_manager.current_experiment_dir)
            
            # Check for gnuplot data files and generated images
            gnuplot_dir = os.path.join(experiment_manager.current_experiment_dir, "gnuplot_data")
            
            if os.path.exists(gnuplot_dir):
                # Scan for data and script files
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
        
        # Add gnuplot data to experiment_summary for frontend compatibility
        experiment_summary['gnuplot_files'] = gnuplot_files
        experiment_summary['generated_images'] = generated_images
        if experiment_id:
            experiment_summary['experiment_info']['experiment_id'] = experiment_id
        
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



# OPTIONS endpoints for experiment management
@app.route('/experiments/<path:endpoint>', methods=['OPTIONS'])
def experiments_options(endpoint):
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/experiments/results/<experiment_id>/large-data/<filename>', methods=['GET'])
def get_experiment_large_data(experiment_id, filename):
    """
    Get large data files for a specific experiment (clustering results, processed data, etc.)
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
        description: The large data filename to retrieve
    responses:
      200:
        description: Large data file content
        schema:
          type: object
      404:
        description: File not found
    """
    try:
        import os
        
        # Construct the path to the large data file
        exp_dir = os.path.join("experiment_results", experiment_id)
        large_data_dir = os.path.join(exp_dir, "large_data")
        file_path = os.path.join(large_data_dir, filename)
        
        # Security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(large_data_dir)):
            return jsonify({
                "status": "error",
                "message": "Invalid file path"
            }), 400
        
        if not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": f"Large data file {filename} not found"
            }), 404
        
        # Load and return the large data file
        with open(file_path, 'r') as f:
            large_data = json.load(f)
        
        file_size = os.path.getsize(file_path)
        
        response = jsonify({
            "status": "success",
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_kb": file_size / 1024,
            "data": large_data
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error loading large data file: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/experiments/results/<experiment_id>/large-data', methods=['GET'])
def list_experiment_large_data_files(experiment_id):
    """
    List all large data files for a specific experiment
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
        description: List of large data files
        schema:
          type: object
          properties:
            status:
              type: string
            files:
              type: array
    """
    try:
        import os
        
        # Construct the path to the large data directory
        exp_dir = os.path.join("experiment_results", experiment_id)
        large_data_dir = os.path.join(exp_dir, "large_data")
        
        if not os.path.exists(large_data_dir):
            return jsonify({
                "status": "success",
                "files": [],
                "message": "No large data directory found - experiment uses standard storage"
            })
        
        # List all JSON files in the large data directory
        large_data_files = []
        for filename in os.listdir(large_data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(large_data_dir, filename)
                file_size = os.path.getsize(file_path)
                file_info = {
                    'filename': filename,
                    'size_bytes': file_size,
                    'size_kb': file_size / 1024,
                    'size_mb': file_size / (1024 * 1024),
                    'type': 'clustering_results' if 'clustering' in filename else 
                           'processed_clusters' if 'processed' in filename else
                           'domain_results' if 'domain' in filename else 
                           'html_files' if 'html' in filename else 'unknown'
                }
                large_data_files.append(file_info)
        
        # Sort files by size (largest first)
        large_data_files.sort(key=lambda x: x['size_bytes'], reverse=True)
        
        total_size = sum(f['size_bytes'] for f in large_data_files)
        
        response = jsonify({
            "status": "success",
            "files": large_data_files,
            "total_files": len(large_data_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "large_data_directory": f"experiment_results/{experiment_id}/large_data/"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error listing large data files: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500



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