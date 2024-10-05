import os
import webbrowser
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import sys

# Add the lib directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from lib import process_urls_from_api

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Enable Swagger only if the environment variable is set
enable_swagger = os.getenv('ENABLE_SWAGGER', 'true').lower() in ['true', '1', 'yes']
swagger = Swagger(app) if enable_swagger else None  # Initialize Swagger if enabled

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
    # results = run_price_processes(urls)
    results = process_urls_from_api(urls, [1])
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