import datetime
import json
import uuid
from utils.image import create_image_by_level
from utils.process import process_url

# Generate a timestamp for the file name
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

class DataCollector:
    def __init__(self):
        self.url_data = {}

    def collect_data(self, urls, driver, config):
        for url in urls:
            unique_id = str(uuid.uuid4())  # Generate a unique identifier            
            self.url_data[unique_id] = {'url': url, 'html_data': {}, 'combinations_by_level': {}}
            process_url(url, driver, config, unique_id, self)
            # create_image_by_level(self, timestamp)


    def save_data(self):
        

        # Save the collected data to a file with the timestamp
        file_name = f"results/data_{timestamp}.json"
        with open(file_name, 'w') as f:
            json.dump(self.url_data, f, indent=4)
