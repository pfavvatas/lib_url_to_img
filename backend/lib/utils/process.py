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
    try:
        driver.get(url)
        # Wait for 10 seconds before proceeding with scraping
        # time.sleep(10)
    except WebDriverException as e:
        with open('errors.log', 'a') as f:
            f.write(f"Error processing URL {url}: {str(e)}\n")
        print('\033[91m' + "Error: " + url + '\033[0m')
        return
    
    #Step 0
    parsed_url = urlparse(url)
    # folder_name = "results/"+ (parsed_url.netloc or 'localhost')
    # os.makedirs(folder_name, exist_ok=True)
    # Replace special characters with underscore
    folder_name = re.sub(r'[/:?#\\[\]@!$&\'()*+,;=]', '_', url)
    # Replace multiple consecutive underscores with a single one
    folder_name = re.sub(r'__+', '_', folder_name)
    folder_name = "results/" + folder_name
    os.makedirs(folder_name, exist_ok=True)

    #Step 1
    tag_name = config.get_attribute('settings.html_parser.tag_name', 'html')
    root = HTMLTag(driver.find_element(By.TAG_NAME, tag_name), driver)
    writeToFile(folder_name, FileNames.DATA.value , FileExtensions.JSON.value , root.to_dict())

    #Step2
    # Generate combinations and their reversed forms with levels
    combinations_reverse = {}
    generate_combinations_reversed(root, [], [], combinations_reverse)
    writeToFile(folder_name, FileNames.COMBINATIONS.value , FileExtensions.JSON.value , combinations_reverse)

    # Step 3
    # Retrieve the level attribute from the configuration. Default to [1] if not found.
    # level = config.get_attribute('settings.level', [1])
    # Generate all available combinations based on the specified level.
    # 'combinations_reverse' is a list of combinations in reverse order.
    # 'root' is the root node for the search.
    combinations_by_level = search_multiple_levels(combinations_reverse, levels, root)

    #Step3.1
    #Lista me olous toys html tag sundiasmous basi unique id apo Step3
    all_combinations_tags_by_unique_id = get_combinations_tags_by_unique_id(combinations_by_level)
    writeToFile(folder_name, FileNames.COMBINATIONS_TAGS_BY_UNIQUE_ID.value , FileExtensions.JSON.value , all_combinations_tags_by_unique_id)
   
    #Step3.2
    #tags configuration file
    root.generate_tag_color_map(all_combinations_tags_by_unique_id, FilePaths.CONFIGURATION.value + FileNames.TAGS.value + FileExtensions.JSON.value)

    #Step3.3
    generate_image_data(combinations_by_level, root)
    writeToFile(folder_name, FileNames.COMBINATIONS_BY_LEVEL.value , FileExtensions.JSON.value , combinations_by_level)

    create_image(combinations_by_level, folder_name)


    dataCollector.url_data[unique_id]['html_data'] = root.to_dict()  # Store HTMLTag data
    dataCollector.url_data[unique_id]['combinations_by_level'] = combinations_by_level  # Store combinations_by_level data
