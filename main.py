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

# def process_url(url, driver, config):
#     try:
#         driver.get(url)
#         # Wait for 10 seconds before proceeding with scraping
#         time.sleep(10)
#     except WebDriverException as e:
#         with open('errors.log', 'a') as f:
#             f.write(f"Error processing URL {url}: {str(e)}\n")
#         print('\033[91m' + "Error: " + url + '\033[0m')
#         return
    
#     #Step 0
#     parsed_url = urlparse(url)
#     folder_name = "results/"+ (parsed_url.netloc or 'localhost')
#     os.makedirs(folder_name, exist_ok=True)

#     #Step 1
#     tag_name = config.get_attribute('settings.html_parser.tag_name', 'html')
#     root = HTMLTag(driver.find_element(By.TAG_NAME, tag_name), driver)
#     writeToFile(folder_name, FileNames.DATA.value , FileExtensions.JSON.value , root.to_dict())

#     #Step2
#     # Generate combinations and their reversed forms with levels
#     combinations_reverse = {}
#     generate_combinations_reversed(root, [], [], combinations_reverse)
#     writeToFile(folder_name, FileNames.COMBINATIONS.value , FileExtensions.JSON.value , combinations_reverse)

#     #Step3
#     #Lista me olous tous diathesimous sunduasmous basi level
#     combinations_by_level = search_multiple_levels(combinations_reverse,[1,2,3,4], root)

#     #Step3.1
#     #Lista me olous toys html tag sundiasmous basi unique id apo Step3
#     all_combinations_tags_by_unique_id = get_combinations_tags_by_unique_id(combinations_by_level)
#     writeToFile(folder_name, FileNames.COMBINATIONS_TAGS_BY_UNIQUE_ID.value , FileExtensions.JSON.value , all_combinations_tags_by_unique_id)
   
#     #Step3.2
#     #tags configuration file
#     root.generate_tag_color_map(all_combinations_tags_by_unique_id, FileNames.TAGS_CONFIGURATION.value + FileExtensions.JSON.value)

#     #Step3.3
#     generate_image_data(combinations_by_level, root)
#     writeToFile(folder_name, FileNames.COMBINATIONS_BY_LEVEL.value , FileExtensions.JSON.value , combinations_by_level)

#     create_image(combinations_by_level, folder_name)


#***************************************************************************************************************#
config = Config('config.json')

debug_mode = getattr(config, 'debug', False)
if debug_mode: print(config)

driver = webdriver.Chrome()

urls = [
    'http://localhost:8888/', 
    'http://localhost:8880' ,
    'http://localhost:8889'
    # , 'http://example.com'
    # , 
    # , 'https://nvd.nist.gov/vuln/detail/CVE-2020-14624'
    ]

#TRY
dataCollector = DataCollector()
dataCollector.collect_data(urls, driver, config)
dataCollector.save_data()
dataCollector.computed_styles(level=1)

# Create the ImageDataCollector instance and process the data
image_data_collector = ImageDataCollector(dataCollector.url_data)

# Save the results to a JSON file
# file_path = "results/image_data.json"
image_data_collector.save_to_json()
image_data_collector.generate_images()
image_data_collector.image_info()

# Access the processed information
# print(image_data_collector.levels_info)


# for url in urls: 
#     process_url(url, driver, config)

driver.close()
