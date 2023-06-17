from url_scrapper import HTMLTag
from config import Config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os
import json
from urllib.parse import urlparse


def process_url(url, driver):
    try:
        driver.get(url)
    except WebDriverException as e:
        with open('errors.log', 'a') as f:
            f.write(f"Error processing URL {url}: {str(e)}\n")
        return
    root = HTMLTag(driver.find_element(By.TAG_NAME, 'html'), driver)
    parsed_url = urlparse(url)
    folder_name = "results/"+ (parsed_url.netloc or 'localhost')
    os.makedirs(folder_name, exist_ok=True)
    with open(os.path.join(folder_name, 'data.json'), 'w') as f:
        json.dump(root.to_dict(), f, indent=4)

config = Config('config.json')

debug_mode = getattr(config, 'debug', False)
if debug_mode: print(config)

driver = webdriver.Chrome()

urls = ['http://localhost:8888']

for url in urls:
    process_url(url, driver)

driver.close()
