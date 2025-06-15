import os
import webbrowser
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from flasgger import Swagger
import sys

# Add the lib directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from lib import process_urls_from_api, process_clusters_from_api

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

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
        
        # Check if file exists
        file_path = os.path.join(OUTPUT_HTML_DIR, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            # Return HTML error page instead of JSON
            return render_template_string(FILE_NOT_FOUND_TEMPLATE, filename=filename), 404
            
        print(f"Serving file: {file_path}")
        return send_from_directory(OUTPUT_HTML_DIR, filename)
    except Exception as e:
        print(f"Error serving file: {str(e)}")
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
    return jsonify(results)
  
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
    return jsonify(results)

def run_price_processes(urls):
    # Dummy implementation, replace with your existing processing logic
    return {url: f"Processed data for {url}" for url in urls}

def open_browser():
    port = int(os.getenv('PORT', 5000))
    webbrowser.open(f'http://localhost:{port}/apidocs')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    open_browser()
    app.run(debug=True, host='0.0.0.0', port=port)