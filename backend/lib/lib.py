# FILE: ./lib/main.py

import argparse
from utils import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os
import json
import time
from urllib.parse import urlparse
import stat
import subprocess
import platform
import traceback
import zipfile
import random
import glob
import shutil
import sys
import html

# Add the project root to Python path to import css_list
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from css_list import VALID_CSS_PROPERTIES

def find_chromedriver(port=9515):
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['where', 'chromedriver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(['which', 'chromedriver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0 and result.stdout:
            chromedriver_path = result.stdout.strip()
            print(f"ChromeDriver found at: {chromedriver_path}")
            
            # Create and start the Service
            service = Service(chromedriver_path, port=port)
            service.start()
            return service
        else:
            print("ChromeDriver not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        

def find_chrome_binary():
    # 1. Check environment variable
    chrome_binary = os.environ.get("CHROME_BINARY")
    if chrome_binary and os.path.exists(chrome_binary):
        return chrome_binary

    # 2. Check common locations
    common_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/opt/google/chrome/chrome"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    # 3. Use 'which'
    for binary in ["google-chrome", "chromium-browser", "chromium"]:
        path = shutil.which(binary)
        if path:
            return path

    raise FileNotFoundError("Could not find Chrome or Chromium binary. Set CHROME_BINARY env variable or install Chrome/Chromium.")

def process_urls_from_cli(urls, levels, from_api=False):
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = Config(config_path)

    debug_mode = getattr(config, 'debug', False)
    if debug_mode: print(config)
        
    service = find_chromedriver()
    if service:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.binary_location = find_chrome_binary()
        print("Using Chrome binary at:", chrome_options.binary_location)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Group URLs by domain
    domain_urls = {}
    for url in urls:
        domain = urlparse(url).netloc
        if domain not in domain_urls:
            domain_urls[domain] = []
        domain_urls[domain].append(url)

    # Process each domain separately
    domain_results = {}
    for domain, domain_url_list in domain_urls.items():
        print(f"Processing domain: {domain}")
        dataCollector = DataCollector()
        dataCollector.collect_data(domain_url_list, levels, driver, config)
        
        # Create domain-specific directory
        domain_dir = f"results/{domain}"
        if not os.path.exists(domain_dir):
            os.makedirs(domain_dir)
            
        # Save domain-specific data
        dataCollector.save_data(domain_dir)
        
        # Process computed styles for each level
        domain_styles = {}
        for level in levels:
            total_unique_attributes, attribute_values, computed_styles_file = dataCollector.computed_styles(level=level, domain=domain)
            domain_styles[level] = {
                'total_unique_attributes': total_unique_attributes,
                'attribute_values': attribute_values,
                'file': computed_styles_file
            }
            
            # Get clustering results
            clustering_results = get_clustering_results(dataCollector.url_data, level)
            
            # Save clustering results to a text file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(script_dir)
            output_dir = os.path.join(backend_dir, 'api', 'results', domain, f"clustered_level_{level}")
            os.makedirs(output_dir, exist_ok=True)
            
            clustering_results_file = os.path.join(output_dir, "clustering_results.txt")
            print(f"\nSaving clustering results to: {clustering_results_file}")
            with open(clustering_results_file, "w", encoding='utf-8') as file:
                for cluster in clustering_results:
                    file.write(f"{json.dumps(cluster)}\n")
            
        # Save image data
        image_data_collector = ImageDataCollector(dataCollector.url_data)
        image_data_collector.save_to_json(domain_dir)
        
        domain_results[domain] = {
            'url_data': dataCollector.url_data,
            'computed_styles': domain_styles
        }
    
    driver.close()    
    
    if from_api:
        return {
            "status": "success", 
            "message": "URLs processed successfully", 
            "domains": domain_results
        }
    else:
        return {"status": "success", "message": "URLs processed successfully"}


def process_clusters_from_cli(clusters_data, from_api=False):
    """
    Process clustering results and generate HTML files with cluster information.
    """
    print("\n=== Starting process_clusters_from_cli ===")
    print(f"Input data type: {type(clusters_data)}")
    print(f"Input data: {clusters_data}")
    
    class Cluster:
        def __init__(self, id, color, guids):
            self.id = id
            self.color = color
            self.guids = guids
            self.additional_info = None

        def set_additional_info(self, info):
            self.additional_info = info

        def __repr__(self):
            return f"Cluster(id={self.id}, color={self.color}, guids={len(self.guids)}, additional_info={self.additional_info})"
        
        def print_results_one_line(self):
            return f"Cluster(id={self.id}, color={self.color}, guids={len(self.guids)}, additional_info={self.additional_info})"
    
    # List of colors for clusters
    colors = [
        "#FFB6C1",  # Light Pink
        "#98FB98",  # Pale Green
        "#87CEFA",  # Light Sky Blue
        "#DDA0DD",  # Plum
        "#F0E68C",  # Khaki
        "#E6E6FA",  # Lavender
        "#FFA07A",  # Light Salmon
        "#B0E0E6",  # Powder Blue
        "#FFE4E1",  # Misty Rose
        "#F0FFF0",  # Honeydew
        "#F5F5DC",  # Beige
        "#E0FFFF",  # Light Cyan
        "#FFF0F5",  # Lavender Blush
        "#F0F8FF",  # Alice Blue
        "#FAFAD2",  # Light Goldenrod Yellow
        "#FFEFD5",  # Peach Puff
        "#F5FFFA",  # Mint Cream
        "#FFF5EE",  # Seashell
        "#F8F8FF",  # Ghost White
        "#FFFAF0",  # Floral White
        "#FFFFF0",  # Ivory
        "#FAFFF0",  # Light Mint
        "#F0FFFA",  # Light Mint Cream
        "#FFF0F8",  # Light Pink
        "#F0F0FF",  # Light Blue
        "#FFFFF5",  # Light Yellow
        "#F5FFF0",  # Light Green
        "#FFF0F0"   # Light Red
    ]
    
    def generate_random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    data_to_return = []
    file_paths = []
    
    # Process each domain's clustering results
    for domain, domain_data in clusters_data.items():
        print(f"\nProcessing domain: {domain}")
        data_to_return.append(f"Processing domain: {domain}")
        
        for level, level_data in domain_data.items():
            print(f"Processing level {level}")
            data_to_return.append(f"Processing level {level}")
            
            # Get the clustering results
            clusters = level_data.get('results', [])
            if not clusters:
                print(f"No clusters found for domain {domain} level {level}")
                continue
                
            # Create Cluster objects
            cluster_objects = []
            for i, guids in enumerate(clusters):
                color = colors[i % len(colors)] if i < len(colors) else generate_random_color()
                print(f"\nCreating cluster {i} with color: {color}")
                cluster = Cluster(id=f"cluster_{i}", color=color, guids=guids)
                cluster_objects.append(cluster)
                data_to_return.append(cluster.print_results_one_line())
            
            # Find the latest data file for this domain and level
            script_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(script_dir)
            domain_dir = os.path.join(backend_dir, 'api', 'results', domain)
            
            print(f"\nLooking for data files in: {domain_dir}")
            if not os.path.exists(domain_dir):
                print(f"Domain directory not found: {domain_dir}")
                continue
            
            # Find the latest data_timestamp.json file
            data_files = glob.glob(os.path.join(domain_dir, "data_*.json"))
            if not data_files:
                print(f"No data files found in {domain_dir}")
                continue
                
            latest_data_file = max(data_files, key=os.path.getmtime)
            print(f"Found latest data file: {latest_data_file}")
            
            # Find the latest computed styles file
            styles_dir = os.path.join(domain_dir, f"computed_styles_level_{level}")
            if not os.path.exists(styles_dir):
                print(f"Styles directory not found: {styles_dir}")
                continue
                
            styles_files = glob.glob(os.path.join(styles_dir, "computed_styles_*.json"))
            if not styles_files:
                print(f"No styles files found in {styles_dir}")
                continue
                
            latest_styles_file = max(styles_files, key=os.path.getmtime)
            print(f"Found latest styles file: {latest_styles_file}")
            
            try:
                # Read the HTML data
                print("\nReading HTML data...")
                with open(latest_data_file, 'r') as file:
                    html_data = json.load(file)
                    print(f"Loaded HTML data with {len(html_data)} URLs")
                
                # Read the computed styles
                print("\nReading computed styles...")
                with open(latest_styles_file, 'r') as file:
                    styles_data = json.load(file)
                    print(f"Loaded styles data with {len(styles_data)} elements")
                
                # Process each element and add cluster information
                print("\nProcessing elements and adding cluster information...")
                def process_element(element_data):
                    if not isinstance(element_data, dict):
                        return
                        
                    unique_id = str(element_data.get("unique_id"))
                    # print(f"Processing element with unique_id: {unique_id} and cluster_objects: {cluster_objects}")
                    for cluster in cluster_objects:
                        if unique_id in cluster.guids:
                            # print(f"Element {unique_id} found in cluster {cluster.id} with color {cluster.color}")
                            if "clusters" not in element_data:
                                element_data["clusters"] = []
                            element_data["clusters"].append(cluster.__dict__)
                    for child in element_data.get("children", []):
                        process_element(child)
                
                # Create output directory
                output_dir = os.path.join(domain_dir, f"clustered_level_{level}")
                print(f"\nCreating output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
                
                # Save clustering results to a text file
                clustering_results_file = os.path.join(output_dir, "clustering_results.txt")
                print(f"\nSaving clustering results to: {clustering_results_file}")
                with open(clustering_results_file, "w", encoding='utf-8') as file:
                    for cluster in clusters:
                        file.write(f"{json.dumps(cluster)}\n")
                
                file_paths.append({
                    'domain': domain,
                    'level': level,
                    'path': f"{domain}/clustered_level_{level}/clustering_results.txt"
                })
                
                # Generate HTML files
                print("\nGenerating HTML files...")
                def create_html_element(element_data, style_map=None):
                    if not isinstance(element_data, dict):
                        return ""
                    
                    tag_name = element_data.get("tag_name", "div")
                    text = html.escape(str(element_data.get("actual_text", "")))
                    children = element_data.get("children", [])
                    attributes = element_data.get("attributes", {})
                    clusters = element_data.get("clusters", [])

                    # Filter out vendor-prefixed styles
                    attributes = {k: v for k, v in attributes.items() if not k.startswith("-webkit")}
                    
                    # Get valid CSS properties
                    styles = {
                        k: str(v) for k, v in attributes.items()
                        if k in VALID_CSS_PROPERTIES
                    }

                    # Generate a unique class name based on styles
                    style_key = ";".join(f"{k}:{v}" for k, v in sorted(styles.items()))
                    if style_key and style_map is not None:
                        if style_key not in style_map:
                            style_map[style_key] = f"style_{len(style_map)}"
                        class_name = style_map[style_key]
                    else:
                        class_name = ""

                    # Add cluster background color
                    if clusters:
                        for cluster in clusters:
                            if 'background-color' not in styles:
                                styles['background-color'] = cluster['color']
                            if style_map is not None:
                                cluster_style_key = f"background-color:{cluster['color']}"
                                if cluster_style_key not in style_map:
                                    style_map[cluster_style_key] = f"cluster_{len(style_map)}"
                                class_name = f"{class_name} {style_map[cluster_style_key]}"

                    # Keep only essential non-style attributes
                    essential_attrs = {'id', 'class', 'href', 'src', 'alt', 'title'}
                    other_attributes = {
                        k: str(v) for k, v in attributes.items() 
                        if k not in VALID_CSS_PROPERTIES and k in essential_attrs
                    }

                    # Build attributes string
                    attr_parts = []
                    if class_name:
                        attr_parts.append(f'class="{class_name}"')
                    for k, v in other_attributes.items():
                        attr_parts.append(f'{k}="{html.escape(v, quote=True)}"')
                    for cluster in clusters:
                        attr_parts.append(f'data-cluster="{html.escape(cluster["id"], quote=True)}"')
                    
                    attributes_str = " ".join(attr_parts)

                    # Render children
                    children_html = "".join(create_html_element(child, style_map) for child in children)

                    # Final HTML
                    return f"<{tag_name} {attributes_str}>{text}{children_html}</{tag_name}>"
                
                # Process each URL's HTML data
                for url, url_data in html_data.items():
                    print(f"\nProcessing URL: {url}")
                    if not isinstance(url_data, dict):
                        continue
                        
                    html_content = url_data.get("html_data", {})
                    if not html_data:
                        print(f"No HTML data for URL: {url}")
                        continue
                    
                    # Process the HTML data with cluster information
                    process_element(html_content)
                    
                    # Generate the HTML file
                    try:
                        # Create a style map to store unique styles
                        style_map = {}
                        
                        # Generate HTML with style map
                        body_content = create_html_element(html_content, style_map)
                        
                        # Generate CSS from style map
                        css_rules = []
                        for style_key, class_name in style_map.items():
                            if style_key.startswith('background-color:'):
                                css_rules.append(f".{class_name} {{ {style_key} }}")
                            else:
                                css_rules.append(f".{class_name} {{ {style_key} }}")
                        
                        css_content = "\n".join(css_rules)
                        
                        final_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Clustered Results - {domain} Level {level}</title>
    <style>
        {css_content}
    </style>
</head>
<body>
    {body_content}
</body>
</html>"""
                        
                        # Create a safe filename from the URL
                        safe_filename = url.replace("://", "_").replace("/", "_").replace(".", "_")
                        output_file = os.path.join(output_dir, f"{safe_filename}.html")
                        print(f"Writing HTML file: {output_file}")
                        
                        with open(output_file, "w", encoding='utf-8') as file:
                            file.write(final_html)
                        
                        data_to_return.append(f"File created: {os.path.abspath(output_file)}")
                        file_paths.append({
                            'domain': domain,
                            'level': level,
                            'path': f"{domain}/clustered_level_{level}/{safe_filename}.html"
                        })
                    except Exception as e:
                        print(f"Error generating HTML for URL {url}: {str(e)}")
                        continue
                
                # Save the processed JSON
                output_json = os.path.join(output_dir, "WEB.json")
                print(f"\nSaving processed JSON to: {output_json}")
                with open(output_json, "w", encoding='utf-8') as file:
                    json.dump(html_data, file, indent=4)
                
                data_to_return.append(f"Results written to: {output_json}")
                
            except Exception as e:
                print(f"Error processing data: {str(e)}")
                continue
    
    print("\n=== End process_clusters_from_cli ===")
    print(f"Generated {len(file_paths)} HTML files")
    return {
        "status": "success", 
        "message": "Clustering completed successfully", 
        "data": json.dumps(data_to_return),
        "file_paths": file_paths
    }

def process_urls_from_api(urls, levels):
    try:
        result = process_urls_from_cli(urls, levels, from_api=True)
        
        # Prepare data for clustering and limit the size
        clustering_data = {}
        domain_summary = {}
        file_paths = []
        
        for domain, domain_data in result['domains'].items():
            # Create a summary of the domain data
            domain_summary[domain] = {
                'url_count': len(domain_data['url_data']),
                'levels_processed': list(domain_data['computed_styles'].keys())
            }
            
            # Prepare clustering data with limited information
            clustering_data[domain] = {}
            for level, level_data in domain_data['computed_styles'].items():
                # Get the attribute values for debugging
                attribute_values = level_data['attribute_values']
                if len(attribute_values) > 1000:
                    attribute_values = attribute_values[:1000]
                
                # Get clustering results (to be implemented)
                clustering_results = get_clustering_results(domain_data['url_data'], level)
                
                # Structure the response
                clustering_data[domain][level] = {
                    'results': clustering_results,
                    # 'debug': {
                    #     'attribute_values': attribute_values
                    # } if getattr(config, 'debug', False) else None
                }
                
                # Add file path to the list
                if 'file' in level_data:
                    file_paths.append({
                        'domain': domain,
                        'level': level,
                        'path': level_data['file']
                    })
        
        # Create a more compact response
        response_data = {
            "status": result.get("status"),
            "message": result.get("message"),
            "summary": {
                "total_domains": len(domain_summary),
                "domains": domain_summary
            },
            "clustering_data": clustering_data,
            "file_paths": file_paths
        }
        
        return response_data
        
    except Exception as e:
        error_message = f"Error processing URLs: {str(e)}"
        stack_trace = traceback.format_exc()
        with open('error.log', 'a') as error_file:
            error_file.write(f"{error_message}\n")
            error_file.write(f"{stack_trace}\n")
        return {
            "status": "error", 
            "message": str(e),
            "stack_trace": stack_trace
        }

def get_clustering_results(url_data, level):
    """
    This function will return clustering results using the clustering module.
    """
    import glob
    import os
    
    print("\n=== Starting get_clustering_results ===")
    print(f"Input level: {level}")
    print(f"Input url_data type: {type(url_data)}")
    print(f"Input url_data keys: {url_data.keys() if isinstance(url_data, dict) else 'Not a dict'}")
    
    # Add the lib directory to Python path
    lib_dir = os.path.dirname(os.path.abspath(__file__))
    if lib_dir not in sys.path:
        sys.path.append(lib_dir)
        print(f"Added {lib_dir} to Python path")
    
    from utils.clustering import process_clustering

    # Get the domain from the first URL in url_data
    domain = None
    if url_data and isinstance(url_data, dict):
        try:
            # Look for URL in the values of url_data
            for value in url_data.values():
                if isinstance(value, dict) and 'url' in value:
                    url = value['url']
                    if isinstance(url, str):
                        domain = urlparse(url).netloc
                        print(f"\nProcessing domain: {domain}")
                        break
            
            if not domain:
                print("No valid URL found in url_data values")
                return []
                
        except Exception as e:
            print(f"Error extracting domain: {str(e)}")
            return []

    if not domain:
        print("No domain found in url_data")
        return []

    # Find the latest computed styles file for this domain and level
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    domain_dir = os.path.join(backend_dir, 'api', 'results', domain)
    level_dir = os.path.join(domain_dir, f"computed_styles_level_{level}")
    
    print(f"\nLooking for computed styles in: {level_dir}")
    
    if not os.path.exists(level_dir):
        print(f"Level directory not found: {level_dir}")
        return []
    
    # Get all JSON files in the level directory
    json_files = glob.glob(os.path.join(level_dir, "computed_styles_*.json"))
    print(f"Found {len(json_files)} JSON files in {level_dir}")
    
    if not json_files:
        print("No computed styles files found!")
        return []
    
    # Get the latest file
    latest_file = max(json_files, key=os.path.getmtime)
    print(f"\nSelected latest file: {latest_file}")

    # Read the computed styles data
    print(f"\nReading computed styles from: {latest_file}")
    with open(latest_file, 'r') as file:
        data = json.load(file)
    print(f"Loaded data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    print(f"Data size: {len(str(data))} bytes")

    # Process the clustering
    print("\nCalling process_clustering...")
    clusters = process_clustering(data)
    print(f"Received {len(clusters)} clusters from process_clustering")
    print("=== End get_clustering_results ===\n")
    
    return clusters

def create_numerical_clusters(html_data, clusters_data):
    """
    Create a numerical representation of clusters for each site.
    Returns a dictionary where each site has a list of cluster IDs in the order elements appear.
    All URLs from all domains are combined into a single 'Sites' dictionary.
    
    Args:
        html_data: Dictionary containing HTML data for each URL
        clusters_data: Dictionary containing cluster results organized by domain and level
    """
    print("\n=== Starting create_numerical_clusters ===")
    print(f"Input html_data type: {type(html_data)}")
    print(f"Input html_data keys: {html_data.keys() if isinstance(html_data, dict) else 'Not a dict'}")
    print(f"Input clusters_data type: {type(clusters_data)}")
    print(f"Input clusters_data structure: {clusters_data}")
    
    # Initialize the Sites dictionary
    sites = {}
    site_counter = 1
    
    # First, create a mapping of element IDs to their cluster positions
    element_to_cluster = {}
    for domain, domain_data in clusters_data.items():
        for level, level_data in domain_data.items():
            clusters = level_data.get('results', [])
            if not clusters:
                continue
            
            # For each cluster array, assign its position number to all elements in it
            for cluster_idx, element_ids in enumerate(clusters, 1):  # Start from 1
                for element_id in element_ids:
                    element_to_cluster[str(element_id)] = cluster_idx
    
    print(f"Created mapping for {len(element_to_cluster)} elements")
    print("Sample of element_to_cluster mapping:", dict(list(element_to_cluster.items())[:5]))
    
    # Process each URL's HTML data
    for url_id, url_data in html_data.items():
        if not isinstance(url_data, dict):
            print(f"Skipping URL ID {url_id}: url_data is not a dict")
            continue
        
        # Get the actual URL from the data
        actual_url = url_data.get('url', '')
        if not actual_url:
            print(f"No URL found in data for ID {url_id}")
            continue
        
        print(f"\nProcessing URL: {actual_url}")
        
        # Get the HTML content
        html_content = url_data.get("html_data", {})
        if not html_content:
            print(f"No HTML content for URL: {actual_url}")
            continue
        
        # Function to traverse the HTML tree and collect cluster numbers
        def traverse_html_tree(element_data, cluster_sequence):
            if not isinstance(element_data, dict):
                return
            
            # Check if this element belongs to a cluster
            unique_id = str(element_data.get("unique_id"))
            if unique_id in element_to_cluster:
                cluster_num = element_to_cluster[unique_id]
                cluster_sequence.append(cluster_num)
                print(f"Found element {unique_id} in cluster {cluster_num}")
            
            # Process children recursively
            for child in element_data.get("children", []):
                traverse_html_tree(child, cluster_sequence)
        
        # Create the sequence for this URL
        cluster_sequence = []
        traverse_html_tree(html_content, cluster_sequence)
        
        if cluster_sequence:
            print(f"Generated cluster sequence of length: {len(cluster_sequence)}")
            print(f"First 10 elements of sequence: {cluster_sequence[:10]}")
            
            # Add to sites with sequential numbering and URL
            site_name = f'Site_{site_counter}_{actual_url}'
            sites[site_name] = cluster_sequence
            print(f"Added sequence as {site_name}")
            site_counter += 1
        else:
            print(f"No cluster sequence generated for URL: {actual_url}")
            print("Available unique_ids in element_to_cluster:", list(element_to_cluster.keys())[:5])
            print("First few unique_ids in HTML content:", [str(child.get("unique_id")) for child in html_content.get("children", [])[:5]])
    
    print("\nFinal sites structure:")
    for site_name, sequence in sites.items():
        print(f"\n{site_name}:")
        print(f"  Sequence length: {len(sequence)}")
        print(f"  First 10 elements: {sequence[:10]}")
    
    print("\n=== End create_numerical_clusters ===")
    return {"Sites": sites}

def process_clusters_from_api(clusters_data):
    try:
        # Process the clusters data and generate HTML files
        result = process_clusters_from_cli(clusters_data, from_api=True)
        
        # Get the HTML data from the latest data file
        html_data = {}
        print("\nLoading HTML data from files...")
        
        for domain, domain_data in clusters_data.items():
            print(f"\nProcessing domain: {domain}")
            # Find the latest data file for this domain
            script_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(script_dir)
            domain_dir = os.path.join(backend_dir, 'api', 'results', domain)
            
            # Find the latest data_timestamp.json file
            data_files = glob.glob(os.path.join(domain_dir, "data_*.json"))
            if data_files:
                latest_data_file = max(data_files, key=os.path.getmtime)
                print(f"\nReading HTML data from: {latest_data_file}")
                try:
                    with open(latest_data_file, 'r') as file:
                        domain_html_data = json.load(file)
                        print(f"Loaded {len(domain_html_data)} URLs for domain {domain}")
                        html_data.update(domain_html_data)
                except Exception as e:
                    print(f"Error reading data file for domain {domain}: {str(e)}")
            else:
                print(f"No data files found for domain {domain}")
        
        print(f"\nTotal HTML data loaded: {len(html_data)} URLs")
        print("Sample of HTML data keys:", list(html_data.keys())[:5] if html_data else "No data")
        
        # Create numerical cluster representation
        numerical_clusters = create_numerical_clusters(html_data, clusters_data)
        
        # Return the results with file paths and numerical clusters
        return {
            "status": result.get("status"), 
            "message": result.get("message"), 
            "body": result.get("data", {}),
            "file_paths": result.get("file_paths", []),
            "numerical_clusters": numerical_clusters
        }
    except Exception as e:
        error_message = f"Error processing clusters: {str(e)}"
        stack_trace = traceback.format_exc()
        with open('error.log', 'a') as error_file:
            error_file.write(f"{error_message}\n")
            error_file.write(f"{stack_trace}\n")
        return {
            "status": "error", 
            "message": str(e),
            "stack_trace": stack_trace
        }

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--urls', type=str, required=True, help='Comma-separated list of URLs')
    parser.add_argument('--levels', type=int, nargs='+', required=True, help='Space-separated list of levels')
    args = parser.parse_args()

    # Convert the comma-separated string of URLs into a list
    urls = args.urls.split(',')

    # Get the levels from the arguments
    levels = args.levels

    process_urls_from_cli(urls, levels)