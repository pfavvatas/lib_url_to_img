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



def find_chromedriver():
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['where', 'chromedriver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(['which', 'chromedriver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0 and result.stdout:
            print(f"ChromeDriver found at: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            print("ChromeDriver not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        

def process_urls_from_cli(urls, levels, from_api=False):
    # config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    # config = Config(config_path)

    # debug_mode = getattr(config, 'debug', False)
    # if debug_mode: print(config)
        
    # chromedriver_path = find_chromedriver()
    
    # if chromedriver_path:
    #     service = Service(chromedriver_path)
    # else:
    #     service = Service('/usr/lib64/chromium/chromedriver')
    # driver = webdriver.Chrome(service=service)

    # dataCollector = DataCollector()
    # dataCollector.collect_data(urls, levels, driver, config)
    # dataCollector.save_data()
    # total_unique_attributes, attribute_values, computed_styles_file = dataCollector.computed_styles(level=1)

    # image_data_collector = ImageDataCollector(dataCollector.url_data)
    # image_data_collector.save_to_json()
    
    # driver.close()
    
    #########################################################################################################################
    # Send the computed styles to the Thanasis script.
    # The Thanasis script will return a list of cluster results in N dimensions.
    # The cluster results will be saved in a file.
    # I will read the file and set the cluster results in the dataCollector object.
    # Define the Cluster class
    class Cluster:
        def __init__(self, id, color, guids):
            self.id = id
            self.color = color
            self.guids = guids
            self.additional_info = None  # Placeholder for additional information

        def set_additional_info(self, info):
            self.additional_info = info

        def __repr__(self):
            return f"Cluster(id={self.id}, color={self.color}, guids={self.guids}, additional_info={self.additional_info})"
    
    data = [
        ["140653470205168", "140652370213280", "140653074663792"],
        ["140652370213616", "140653431161760", "140652370210928"],
        ["140653431161616", "140653431163488", "140653431163632"]
    ]
    
    # List of 30 different colors
    colors = [
        "red", "blue", "green", "yellow", "purple", "orange", "pink", "brown", "black", "white",
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

    # Print clusters to verify
    for cluster in clusters:
        print(cluster)
        
    # Collect all GUIDs from clusters
    all_guids = set()
    for cluster in clusters:
        all_guids.update(cluster.guids) 
          
    # Function to recursively search for unique_id in html_data
    def search_html_data(html_data, guids):
        unique_id = str(html_data.get("unique_id"))
        if unique_id in guids:
            return {
                "unique_id": html_data.get("unique_id"),
                "tag_name": html_data.get("tag_name"),
                "text": html_data.get("text"),
                "text_size": html_data.get("text_size"),
                "attributes": html_data.get("attributes")
            }
        for child in html_data.get("children", []):
            result = search_html_data(child, guids)
            if result:
                print(f"Found GUID: {result['unique_id']}")
                return result
        return None

    # Read the JSON file
    file_path = "/home/pfavvatas/lib_url_to_img/backend/api/results/data_20241010181246.json"

    # Check if the file exists
    if os.path.exists(file_path):
        # Get the file size
        file_size = os.path.getsize(file_path)
        
        # Read the JSON file and count the number of top-level keys
        with open(file_path, "r") as file:
            json_data = json.load(file)
            num_keys = len(json_data)
        
        print(f"File found: {file_path}")
        print(f"File size: {file_size} bytes")
        print(f"Number of top-level keys (GUIDs): {num_keys}")
    else:
        print(f"File not found: {file_path}")
        return {"status": "error", "message": "File not found"}

    # Create a dictionary to map unique_id to its corresponding data
    unique_id_map = {}
    for key, guid_data in json_data.items():
        html_data = guid_data.get("html_data")
        if html_data:
            print(f"Processing GUID: {key} for URL: {guid_data.get('url')}")
            result = search_html_data(html_data, all_guids)
            if result:
                # print(f"Result: {result}")
                result["url"] = guid_data.get("url")
                unique_id_map[str(result["unique_id"])] = result  # Ensure keys are strings
    print(f"Number of unique IDs found: {len(unique_id_map)}")
    print(f"Unique IDs: {unique_id_map.keys()}")
    
    # Extract and print the results
    results = []
    unique_id_keys = set(unique_id_map.keys()) 

    data_to_return = ""
    try:
        for cluster in clusters:
            for guid in cluster.guids:
                guid_str = str(guid)
                print(f"Processing GUID: {guid_str} to find in unique_id_map: {guid_str in unique_id_keys}")
                if guid_str in unique_id_keys:
                    try:
                        data_to_return = unique_id_map
                        # print(type(unique_id_map))
                        # print(type(unique_id_map.items()))
                        # print("guid_str type ",type(guid_str))
                        result = unique_id_map[guid_str]
                        result["cluster_id"] = cluster.id
                        result["cluster_color"] = cluster.color
                        results.append(result)
                    except Exception as e:
                        return {"status": "error", "message": str(e), "stack_trace": traceback.format_exc()}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"status": "error", "message": str(e), "stack_trace": traceback.format_exc()}

    print(f"Number of results: {len(results)}")
    
    # Print results to terminal
    for result in results:
        print(result)

    # Write results to a file
    output_file_path = "/home/pfavvatas/lib_url_to_img/backend/api/results/WEB_results_01.json"
    with open(output_file_path, "w") as file:
        json.dump(results, file, indent=4)
        
    print(f"Results written to: {output_file_path}")

    return {"status": "success", "message": "URLs processed successfully", "data": data_to_return}
    #########################################################################################################################
    
    
    
    
    # if from_api:
    #     return {"status": "success", "message": "URLs processed successfully", "file": computed_styles_file}
    # else:
    #     return {"status": "success", "message": "URLs processed successfully"}

def process_urls_from_api(urls, levels):
    try:
        result = process_urls_from_cli(urls, levels, from_api=True)
        
        # computed_styles_file = result.get("file")

        # # Create a zip file containing the computed styles file
        # zip_filename = "computed_styles.zip"
        # with zipfile.ZipFile(zip_filename, 'w') as zipf:
        #     zipf.write(computed_styles_file, os.path.basename(computed_styles_file))

        # # Read the zip file into a byte array
        # with open(zip_filename, 'rb') as zipf:
        #     zip_data = zipf.read()

        # # Convert the byte array to a hex string
        # zip_hex_data = zip_data.hex()

        # Delete the zip file
        # os.remove(zip_filename)
        
        return {
            "status": result.get("status"), 
            "message": result.get("message"), 
            "body": result.get("data", {}),
            # "files": [{"filename": zip_filename, "data": zip_hex_data}]
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