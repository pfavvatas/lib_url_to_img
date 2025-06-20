from utils import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import time
from urllib.parse import urlparse
import re


def process_url(url, levels, driver, config, unique_id, dataCollector):
    # Initialize timing for this URL
    url_timing = {
        "url": url,
        "unique_id": unique_id,
        "start_time": time.time(),
        "steps": {},
        "file_operations": {},
        "total_duration": 0
    }
    
    # Step 0: Browser navigation
    step_start = time.time()
    try:
        driver.get(url)
        # Wait for 10 seconds before proceeding with scraping
        # time.sleep(10)
        url_timing["steps"]["browser_navigation"] = {
            "start_time": step_start,
            "end_time": time.time(),
            "duration": time.time() - step_start,
            "description": "Browser navigation to URL"
        }
    except WebDriverException as e:
        with open('errors.log', 'a') as f:
            f.write(f"Error processing URL {url}: {str(e)}\n")
        print('\033[91m' + "Error: " + url + '\033[0m')
        url_timing["steps"]["browser_navigation"] = {
            "start_time": step_start,
            "end_time": time.time(),
            "duration": time.time() - step_start,
            "description": "Browser navigation to URL",
            "error": str(e)
        }
        return
    
    # Step 0.1: URL parsing and folder creation
    step_start = time.time()
    parsed_url = urlparse(url)
    # folder_name = "results/"+ (parsed_url.netloc or 'localhost')
    # os.makedirs(folder_name, exist_ok=True)
    # Replace special characters with underscore
    folder_name = re.sub(r'[/:?#\\[\]@!$&\'()*+,;=]', '_', url)
    # Replace multiple consecutive underscores with a single one
    folder_name = re.sub(r'__+', '_', folder_name)
    folder_name = "results/" + folder_name
    os.makedirs(folder_name, exist_ok=True)
    
    url_timing["steps"]["url_parsing"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "URL parsing and folder creation",
        "folder_name": folder_name
    }

    # Step 1: HTML parsing and data extraction
    step_start = time.time()
    tag_name = config.get_attribute('settings.html_parser.tag_name', 'html')
    root = HTMLTag(driver.find_element(By.TAG_NAME, tag_name), driver)
    
    # File operation timing
    file_start = time.time()
    writeToFile(folder_name, FileNames.DATA.value , FileExtensions.JSON.value , root.to_dict())
    file_duration = time.time() - file_start
    
    url_timing["steps"]["html_parsing"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "HTML parsing and data extraction",
        "tag_name": tag_name,
        "file_operation": {
            "duration": file_duration,
            "file_name": f"{FileNames.DATA.value}.{FileExtensions.JSON.value}"
        }
    }
    url_timing["file_operations"]["data_file"] = {
        "duration": file_duration,
        "file_name": f"{FileNames.DATA.value}.{FileExtensions.JSON.value}",
        "folder": folder_name
    }

    # Step 2: Combinations generation
    step_start = time.time()
    # Generate combinations and their reversed forms with levels
    combinations_reverse = {}
    generate_combinations_reversed(root, [], [], combinations_reverse)
    
    # File operation timing
    file_start = time.time()
    writeToFile(folder_name, FileNames.COMBINATIONS.value , FileExtensions.JSON.value , combinations_reverse)
    file_duration = time.time() - file_start
    
    url_timing["steps"]["combinations_generation"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Combinations generation and reversed forms",
        "combinations_count": len(combinations_reverse),
        "file_operation": {
            "duration": file_duration,
            "file_name": f"{FileNames.COMBINATIONS.value}.{FileExtensions.JSON.value}"
        }
    }
    url_timing["file_operations"]["combinations_file"] = {
        "duration": file_duration,
        "file_name": f"{FileNames.COMBINATIONS.value}.{FileExtensions.JSON.value}",
        "folder": folder_name
    }

    # Step 3: Level-based combinations search
    step_start = time.time()
    # Retrieve the level attribute from the configuration. Default to [1] if not found.
    # level = config.get_attribute('settings.level', [1])
    # Generate all available combinations based on the specified level.
    # 'combinations_reverse' is a list of combinations in reverse order.
    # 'root' is the root node for the search.
    combinations_by_level = search_multiple_levels(combinations_reverse, levels, root)
    
    url_timing["steps"]["level_combinations_search"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Level-based combinations search",
        "levels_processed": levels,
        "combinations_by_level_count": len(combinations_by_level)
    }

    # Step 3.1: Combinations tags by unique ID
    step_start = time.time()
    #Lista me olous toys html tag sundiasmous basi unique id apo Step3
    all_combinations_tags_by_unique_id = get_combinations_tags_by_unique_id(combinations_by_level)
    
    # File operation timing
    file_start = time.time()
    writeToFile(folder_name, FileNames.COMBINATIONS_TAGS_BY_UNIQUE_ID.value , FileExtensions.JSON.value , all_combinations_tags_by_unique_id)
    file_duration = time.time() - file_start
    
    url_timing["steps"]["combinations_tags_by_unique_id"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Combinations tags by unique ID generation",
        "unique_ids_count": len(all_combinations_tags_by_unique_id),
        "file_operation": {
            "duration": file_duration,
            "file_name": f"{FileNames.COMBINATIONS_TAGS_BY_UNIQUE_ID.value}.{FileExtensions.JSON.value}"
        }
    }
    url_timing["file_operations"]["combinations_tags_file"] = {
        "duration": file_duration,
        "file_name": f"{FileNames.COMBINATIONS_TAGS_BY_UNIQUE_ID.value}.{FileExtensions.JSON.value}",
        "folder": folder_name
    }
   
    # Step 3.2: Tag color map generation
    step_start = time.time()
    #tags configuration file
    root.generate_tag_color_map(all_combinations_tags_by_unique_id, FilePaths.CONFIGURATION.value + FileNames.TAGS.value + FileExtensions.JSON.value)
    
    url_timing["steps"]["tag_color_map_generation"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Tag color map generation",
        "file_name": f"{FilePaths.CONFIGURATION.value}{FileNames.TAGS.value}{FileExtensions.JSON.value}"
    }

    # Step 3.3: Image data generation
    step_start = time.time()
    generate_image_data(combinations_by_level, root)
    
    # File operation timing
    file_start = time.time()
    writeToFile(folder_name, FileNames.COMBINATIONS_BY_LEVEL.value , FileExtensions.JSON.value , combinations_by_level)
    file_duration = time.time() - file_start
    
    url_timing["steps"]["image_data_generation"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Image data generation",
        "file_operation": {
            "duration": file_duration,
            "file_name": f"{FileNames.COMBINATIONS_BY_LEVEL.value}.{FileExtensions.JSON.value}"
        }
    }
    url_timing["file_operations"]["combinations_by_level_file"] = {
        "duration": file_duration,
        "file_name": f"{FileNames.COMBINATIONS_BY_LEVEL.value}.{FileExtensions.JSON.value}",
        "folder": folder_name
    }

    # Step 4: Image creation
    step_start = time.time()
    create_image(combinations_by_level, folder_name)
    
    url_timing["steps"]["image_creation"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Image creation from combinations"
    }

    # Step 5: Data storage
    step_start = time.time()
    dataCollector.url_data[unique_id]['html_data'] = root.to_dict()  # Store HTMLTag data
    dataCollector.url_data[unique_id]['combinations_by_level'] = combinations_by_level  # Store combinations_by_level data
    
    url_timing["steps"]["data_storage"] = {
        "start_time": step_start,
        "end_time": time.time(),
        "duration": time.time() - step_start,
        "description": "Storing data in collector"
    }

    # Calculate total duration
    url_timing["total_duration"] = time.time() - url_timing["start_time"]
    url_timing["end_time"] = time.time()
    
    # Store timing in dataCollector
    if not hasattr(dataCollector, 'url_timing_logs'):
        dataCollector.url_timing_logs = {}
    dataCollector.url_timing_logs[unique_id] = url_timing
    
    return url_timing
