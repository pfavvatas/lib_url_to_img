from utils import *#HTMLTag, Config, generate_combinations_reversed, writeToFile, FileExtensions, FileNames, search_combinations_by_length, search_multiple_lengths
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os
import json
from urllib.parse import urlparse

def process_url(url, driver, config):
    try:
        driver.get(url)
    except WebDriverException as e:
        with open('errors.log', 'a') as f:
            f.write(f"Error processing URL {url}: {str(e)}\n")
        print('\033[91m' + "Error: " + url + '\033[0m')
        return
    
    #Step 0
    parsed_url = urlparse(url)
    folder_name = "results/"+ (parsed_url.netloc or 'localhost')
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

    #Step3
    combinations_by_length = search_multiple_lengths(combinations_reverse,[1,2,3])
    writeToFile(folder_name, FileNames.COMBINATIONS_BY_LENGTH.value , FileExtensions.JSON.value , combinations_by_length)

#***************************************************************************************************************#
config = Config('config.json')

debug_mode = getattr(config, 'debug', False)
if debug_mode: print(config)

driver = webdriver.Chrome()

urls = ['http://localhost:8888']

for url in urls:
    process_url(url, driver, config)

driver.close()
