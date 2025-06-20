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

# Initialize cache manager
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cache_manager = CacheManager(cache_dir=os.path.join(PROJECT_ROOT, "backend", "api", "cache"))

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