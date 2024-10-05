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
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = Config(config_path)

    debug_mode = getattr(config, 'debug', False)
    if debug_mode: print(config)
        
    chromedriver_path = find_chromedriver()
    
    if chromedriver_path:
        service = Service(chromedriver_path)
    else:
        service = Service('/usr/lib64/chromium/chromedriver')
    driver = webdriver.Chrome(service=service)

    dataCollector = DataCollector()
    dataCollector.collect_data(urls, levels, driver, config)
    dataCollector.save_data()
    total_unique_attributes, attribute_values, computed_styles_file = dataCollector.computed_styles(level=1)

    image_data_collector = ImageDataCollector(dataCollector.url_data)
    image_data_collector.save_to_json()

    driver.close()

    if from_api:
        return {"status": "success", "message": "URLs processed successfully", "file": computed_styles_file}
    else:
        return {"status": "success", "message": "URLs processed successfully"}

def process_urls_from_api(urls, levels):
    try:
        result = process_urls_from_cli(urls, levels, from_api=True)
        computed_styles_file = result.get("file")

        # Create a zip file containing the computed styles file
        zip_filename = "computed_styles.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            zipf.write(computed_styles_file, os.path.basename(computed_styles_file))

        # Read the zip file into a byte array
        with open(zip_filename, 'rb') as zipf:
            zip_data = zipf.read()

        # Convert the byte array to a hex string
        zip_hex_data = zip_data.hex()

        # Delete the zip file
        # os.remove(zip_filename)
        
        return {
            "status": result.get("status"), 
            "message": result.get("message"), 
            "body": {},
            "files": [{"filename": zip_filename, "data": zip_hex_data}]
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