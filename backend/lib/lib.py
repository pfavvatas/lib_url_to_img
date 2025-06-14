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
from utils.clustering import perform_clustering_analysis




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
        chrome_options.binary_location = "/opt/google/chrome/chrome"  # Specify the correct path to your Chrome binary
        driver = webdriver.Chrome(service=service, options=chrome_options)
    

    dataCollector = DataCollector()
    dataCollector.collect_data(urls, levels, driver, config)
    dataCollector.save_data()
    total_unique_attributes, attribute_values, computed_styles_file = dataCollector.computed_styles(level=1)
    for level in levels:
        dataCollector.computed_styles(level=level)

    image_data_collector = ImageDataCollector(dataCollector.url_data)
    image_data_collector.save_to_json()
    
    driver.close()    
    
    # Clustering
    # Process computed styles for each level
    clustering_results = []
    processed_clusters_data = []
    for level in levels:
        # Get the computed styles file path for this level
        computed_styles_file = dataCollector.computed_styles(level=level)[2]
        print(f"\033[92m computed_styles_file: {computed_styles_file}\033[0m")

        # Process the computed styles file and call clustering function directly
        try:
            # Read the computed styles data
            with open(computed_styles_file, 'r') as file:
                data = json.load(file)
            
            print(f"\033[94m=== CLUSTERING RESULTS FOR LEVEL {level} ===\033[0m")
            print(f"\033[92mComputed styles file: {computed_styles_file}\033[0m")
            
            # Call the clustering function with the data directly
            clustering_result = perform_clustering_analysis(data)
            
            if clustering_result['success']:
                print(f"\033[92mStatus: success\033[0m")
                print(f"\033[92mMessage: {clustering_result['message']}\033[0m")
                
                print(f"\033[93mNumber of clusters: {clustering_result['cluster_info']['num_clusters']}\033[0m")
                print(f"\033[93mDBCV Score: {clustering_result['cluster_info']['dbcv_score']:.3f}\033[0m")
                print(f"\033[93mClusters: {clustering_result['clusters']}\033[0m")
                
                # Add level information to the result
                clustering_result['level'] = level
                clustering_results.append(clustering_result)

                # Process clusters for this level
                if 'clusters' in clustering_result:
                    cluster_data = json.dumps(clustering_result['clusters'])
                    processed_cluster = process_clusters_from_cli(cluster_data, from_api=True)
                    processed_clusters_data.append({
                        'level': level,
                        'processed_data': processed_cluster
                    })
            else:
                clustering_results.append({
                    "level": level,
                    "status": "error",
                    "message": f"Level {level}: {clustering_result['message']}"
                })
            
            print(f"\033[94m=== END CLUSTERING RESULTS ===\033[0m\n")
            
        except Exception as e:
            print(f"\033[91mError during clustering: {str(e)}\033[0m")
            clustering_results.append({
                "level": level,
                "status": "error",
                "message": f"Level {level}: Error during clustering: {str(e)}"
            })
    
    if from_api:
        return {
            "status": "success", 
            "message": "URLs processed successfully", 
            "file": computed_styles_file, 
            "clustering_results": clustering_results,
            "processed_clusters": processed_clusters_data
        }
    else:
        return {
            "status": "success", 
            "message": "URLs processed successfully", 
            "clustering_results": clustering_results,
            "processed_clusters": processed_clusters_data
        }


def process_clusters_from_cli(clusters_data, from_api=False):
    class Cluster:
        def __init__(self, id, color, guids):
            self.id = id
            self.color = color
            self.guids = guids
            self.additional_info = None  # Placeholder for additional information

        def set_additional_info(self, info):
            self.additional_info = info

        def __repr__(self):
            return f"Cluster(id={self.id}, color={self.color}, guids={len(self.guids)}, additional_info={self.additional_info})"
        
        def print_results_one_line(self):
            return f"Cluster(id={self.id}, color={self.color}, guids={len(self.guids)}, additional_info={self.additional_info})"
        
    # Custom JSON encoder for Cluster objects
    class ClusterEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Cluster):
                return obj.__dict__
            return super().default(obj)
        
    data = clusters_data
    data = json.loads(data)
        
    # List of 30 different colors
    colors = [
        "red", "blue", "green", "yellow", "purple", "orange", "pink", "brown", #"black", "white",
        "gray", "cyan", "magenta", "lime", "maroon", "navy", "olive", "teal", "aqua", "fuchsia",
        "silver", "gold", "beige", "coral", "indigo", "ivory", "khaki", "lavender", "plum", "salmon"
    ]
    
    # Function to generate a random color
    def generate_random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    # Create Cluster objects from data
    clusters = []
    for i, guids in enumerate(data):
        if i < len(colors):
            color = colors[i]
        else:
            color = generate_random_color()
        cluster = Cluster(id=f"cluster_{i}", color=color, guids=guids)
        clusters.append(cluster)
        
    data_to_return = []
    # Print clusters to verify
    for cluster in clusters:
        print(cluster)
        data_to_return.append(cluster.print_results_one_line())
        
    # Collect all GUIDs from clusters
    all_cluster_guids = set()
    for cluster in clusters:
        all_cluster_guids.update(cluster.guids) 

    # Dictionary to store site-to-cluster mappings
    sites = {}
          
    # Function to search for HTML data with a specific GUID
    def search_html_data(html_data, site_url):
        unique_id = str(html_data.get("unique_id"))
        if unique_id in all_cluster_guids:
            try:
                for cluster in clusters:
                    if unique_id in cluster.guids:
                        cluster_id = int(cluster.id.split('_')[1]) + 1  # Extract the number from cluster_id and add 1
                        if site_url not in sites:
                            sites[site_url] = []
                        sites[site_url].append(cluster_id)
                        if "clusters" not in html_data:
                            html_data["clusters"] = []
                        html_data["clusters"].append(cluster.__dict__)
                        break
            except Exception as e:
                print(f"An error occurred: {e}")
                data_to_return.append(f"An error occurred: {e}")
        for child in html_data.get("children", []):
            search_html_data(child, site_url)

    # Read the JSON file
    def find_latest_data_file(directory):
        search_pattern = os.path.join(directory, "data_*.json")
        files = glob.glob(search_pattern)
        if not files:
            return None
        latest_file = max(files, key=os.path.getmtime)
        return latest_file

    directory = "/home/pfavv/lib_url_to_img/backend/api/results"
    file_path = find_latest_data_file(directory)

    # Check if the file exists
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        with open(file_path, "r") as file:
            json_data = json.load(file)
            num_keys = len(json_data)
        
        print(f"File found: {file_path}")
        print(f"File size: {file_size} bytes")
        print(f"Number of top-level keys (GUIDs): {num_keys}")
        data_to_return.append(f"File found: {file_path}")
        data_to_return.append(f"File size: {file_size} bytes")
        data_to_return.append(f"Number of top-level keys (GUIDs): {num_keys}")
    else:
        print(f"File not found: {file_path}")
        data_to_return.append(f"File not found: {file_path}")
        return {"status": "error", "message": "File not found", "data": data_to_return}

    # Process the JSON data
    for key, guid_data in json_data.items():
        html_data = guid_data.get("html_data")
        if html_data:
            site_url = guid_data.get('url', '')
            print(f"Processing GUID: {key} for URL: {site_url}")
            data_to_return.append(f"Processing GUID: {key} for URL: {site_url}")
            search_html_data(html_data, site_url)
        if "combinations_by_level" in guid_data:
            guid_data.pop("combinations_by_level")

    # Format sites as a string object
    sites_str = "sites = {\n"
    for site_url, cluster_ids in sites.items():
        sites_str += f"    '{site_url}': {cluster_ids},\n"
    sites_str += "}"
    
    # Print the sites mapping
    print("\n" + sites_str)
    data_to_return.append(sites_str)

    # List of valid CSS properties
    VALID_CSS_PROPERTIES = [
        # Fonts and Text
        "font-family", "font-size", "font-weight", "font-style", "font-variant", 
        "font-size-adjust", "font-stretch", "font-feature-settings", "color", 
        "text-align", "text-decoration", "text-transform", "text-shadow", 
        "letter-spacing", "line-height", "white-space", "word-spacing", 
        "word-wrap", "word-break", "overflow-wrap", "hyphens", "direction",

        # Backgrounds and Borders
        "background-color", "background-image", "background-position", 
        "background-repeat", "background-size", "background-attachment", 
        "border", "border-width", "border-style", "border-color", 
        "border-top", "border-right", "border-bottom", "border-left", 
        "border-radius", "border-collapse", "box-shadow", "outline", 
        "outline-color", "outline-style", "outline-width",

        # Margins and Padding
        "margin", "margin-top", "margin-right", "margin-bottom", "margin-left", 
        "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",

        # # Display and Positioning
        # "display", "position", "top", "right", "bottom", "left", "z-index", 
        # "float", "clear", "visibility", "overflow", "overflow-x", "overflow-y", 
        # "clip", "vertical-align",

        # # Flexbox
        # "flex", "flex-grow", "flex-shrink", "flex-basis", "flex-direction", 
        # "flex-wrap", "align-items", "align-content", "justify-content", 
        # "order", "align-self",

        # # Grid
        # "grid", "grid-template-columns", "grid-template-rows", 
        # "grid-template-areas", "grid-column", "grid-row", "grid-gap", 
        # "grid-auto-columns", "grid-auto-rows", "grid-column-start", 
        # "grid-column-end", "grid-row-start", "grid-row-end", 
        # "place-items", "place-content", "place-self",

        # # Sizing
        # "width", "height", "min-width", "min-height", "max-width", "max-height",

        # # Animations and Transitions
        # "animation", "animation-name", "animation-duration", 
        # "animation-timing-function", "animation-delay", "animation-iteration-count", 
        # "animation-direction", "animation-fill-mode", "transition", 
        # "transition-property", "transition-duration", "transition-timing-function", 
        # "transition-delay",

        # # Transforms
        # "transform", "transform-origin", "transform-style", "perspective", 
        # "perspective-origin",

        # # Columns
        # "columns", "column-width", "column-count", "column-gap", 
        # "column-rule", "column-rule-width", "column-rule-style", "column-rule-color",

        # # Tables
        # "table-layout", "border-spacing", "border-collapse", "caption-side", 
        # "empty-cells",

        # # Lists
        # "list-style", "list-style-type", "list-style-position", "list-style-image",

        # # Content and Cursor
        # "content", "quotes", "cursor", "caret-color",

        # # Misc
        # "opacity", "visibility", "pointer-events", "filter", "resize", 
        # "user-select", "will-change", "zoom",

        # Vendor-specific prefixes
        # "-webkit-transform", "-webkit-transition", "-webkit-animation", 
        # "-webkit-box-shadow", "-webkit-border-radius", "-webkit-opacity", 
        # "-webkit-flex", "-webkit-align-items", "-webkit-justify-content", 
        # "-webkit-align-self", "-webkit-order", "-webkit-flex-grow", 
        # "-webkit-flex-shrink", "-webkit-flex-basis", "-webkit-perspective", 
        # "-webkit-perspective-origin", "-webkit-backface-visibility", 
        # "-webkit-box-sizing", "-webkit-text-fill-color", "-webkit-text-stroke", 
        # "-webkit-text-stroke-width", "-webkit-appearance", "-webkit-mask", 
        # "-webkit-mask-image", "-webkit-mask-position", "-webkit-mask-size", 
        # "-webkit-mask-repeat", "-webkit-mask-clip", "-webkit-mask-origin", 
        # "-webkit-mask-composite", "-webkit-box-flex", "-webkit-box-align", 
        # "-webkit-box-pack", "-webkit-box-orient", "-webkit-box-direction", 
        # "-webkit-box-decoration-break", "-webkit-background-clip", 
        # "-webkit-filter", "-webkit-hyphens", "-webkit-overflow-scrolling", 
        # "-webkit-tap-highlight-color", "-webkit-touch-callout", 
        # "-webkit-writing-mode", "-webkit-transition-timing-function", 
        # "-webkit-transition-duration", "-webkit-transition-property", 
        # "-webkit-transition-delay", "-webkit-animation-delay", 
        # "-webkit-animation-duration", "-webkit-animation-iteration-count", 
        # "-webkit-animation-timing-function", "-webkit-animation-name"
    ]
    
    def escape_quotes(value):
        if not isinstance(value, str):
            value = str(value)
        return value.replace('"', "'")
    
    def create_html_from_json(json_data, output_dir):
        def create_element(element_data):
            unique_id = element_data.get("unique_id", None)
            tag_name = element_data.get("tag_name", "div")
            text = element_data.get("actual_text", "")
            children = element_data.get("children", [])
            attributes = element_data.get("attributes", {})
            clusters = element_data.get("clusters", [])
            
            # if len(clusters) > 0:
            #     print(f"Clusters found: {len(clusters)}")
            # if len(clusters) == 0:
            #     return f''
            
            #remove from attributes start with -webkit
            attributes = {key: value for key, value in attributes.items() if not key.startswith("-webkit")}
            
            # Separate CSS styles from other attributes
            styles = {key: value for key, value in attributes.items() if key in VALID_CSS_PROPERTIES}
            other_attributes = {key: value for key, value in attributes.items() if key not in VALID_CSS_PROPERTIES}
    
            # Convert styles dictionary to a string of valid CSS styles
            style_str = "; ".join(f'{key}: {escape_quotes(value)}' for key, value in styles.items())
            if(len(clusters) > 0):
                for cluster in clusters:                    
                    style_str += f"; background-color: {cluster['color']}"
    
            # Convert other attributes dictionary to a string of HTML attributes
            attributes_str = " ".join(
                f'{key}="{escape_quotes(value)}"' for key, value in other_attributes.items()
            )
            
            # if(len(clusters) > 0):
            #     for cluster in clusters:
            #         if unique_id in cluster["guids"]:
            #             style_str += f"; background-color: {cluster['color']}"
            #             attributes_str += f' data-cluster="{cluster["id"]}"'
            
            if(len(clusters) > 0):
                for cluster in clusters:
                    attributes_str += f' data-cluster="{cluster["id"]}"'
            
            children_html = "".join(create_element(child) for child in children)
            
            if(len(clusters) == 0):
                return f'<{tag_name}">{children_html}</{tag_name}>'
            return f'<{tag_name} style="{style_str}"  {attributes_str}>{text}{children_html}</{tag_name}>'
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for key, guid_data in json_data.items():
            html_data = guid_data.get("html_data", {})
            html_content = create_element(html_data)
            
            # Only generate the body part
            final_html = f"<html>{html_content}</html>"
            
            output_file = os.path.join(output_dir, f"{key}.html")
            
            with open(output_file, "w") as file:
                file.write(final_html)
            
            print(f"File created: {output_file}")
            data_to_return.append(f"File created: {os.path.abspath(output_file)}")
            #pathlib.Path(__file__).parent.resolve()
            # print(f"File created: {os.path.abspath(output_file)}")
    

    create_html_from_json(json_data, "output_html_files")
        
    # Write results to a file
    output_file_path = "/home/pfavv/lib_url_to_img/backend/api/results/WEB.json"
    with open(output_file_path, "w") as file:
        json.dump(json_data, file, indent=4)

    print(f"Results written to: {output_file_path}")
    data_to_return.append(f"Results written to: {output_file_path}")

    return {
        "status": "success", 
        "message": "Clustering completed successfully", 
        "data": json.dumps(data_to_return),
        "sites": sites
    }

def process_urls_from_api(urls, levels):
    try:
        result = process_urls_from_cli(urls, levels, from_api=True)
        
        return {
            "status": result.get("status"), 
            "message": result.get("message"), 
            "body": result.get("data", {}),
            "clustering_results": result.get("clustering_results", {}),
            "processed_clusters": result.get("processed_clusters", {})
        }
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


def process_clusters_from_api(clusters_data):
    try:
        result = process_clusters_from_cli(clusters_data, from_api=True)
        
        return {
            "status": result.get("status"), 
            "message": result.get("message"), 
            "body": result.get("data", {})
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