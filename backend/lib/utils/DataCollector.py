import datetime
import json
import uuid
import pandas as pd
import matplotlib.pyplot as plt
import os
import traceback
from utils.image import create_image_by_level
from utils.process import process_url
import time
import random
# Generate a timestamp for the file name
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Set to store used IDs
used_ids = set()

def generate_unique_id():
    while True:
        # Get the current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        # Generate a larger random number for more entropy
        random_number = random.randint(1000000000, 9999999999)
        # Combine the timestamp and the random number
        unique_id = int(f"{timestamp}{random_number}")
        # Check if the ID is unique
        if unique_id not in used_ids:
            used_ids.add(unique_id)
            return unique_id
        else:
            print(f"\033[93mDuplicate ID found: {unique_id}, generating a new one.\033[0m")

class DataCollector:
    def __init__(self):
        self.url_data = {}
        self.timing_logs = {
            "start_time": time.time(),
            "url_processing": {},
            "total_urls": 0
        }

    def collect_data(self, urls, levels, driver, config):
        self.timing_logs["total_urls"] = len(urls)
        self.timing_logs["levels"] = levels
        self.url_timing_logs = {}  # Store detailed timing for each URL
        
        for i, url in enumerate(urls):
            url_start_time = time.time()
            unique_id = generate_unique_id()  # Generate a unique identifier            
            self.url_data[unique_id] = {'url': url, 'html_data': {}, 'combinations_by_level': {}}
            
            # Process the URL
            url_timing_result = process_url(url, levels, driver, config, unique_id, self)
            
            # Record timing for this URL
            url_duration = time.time() - url_start_time
            self.timing_logs["url_processing"][f"url_{i+1}"] = {
                "url": url,
                "unique_id": unique_id,
                "start_time": url_start_time,
                "end_time": time.time(),
                "duration": url_duration,
                "description": f"Processing URL {i+1} of {len(urls)}",
                "detailed_timing": url_timing_result  # Include the detailed timing from process_url
            }
            
            print(f"Processed URL {i+1}/{len(urls)}: {url} (took {url_duration:.2f}s)")
            # create_image_by_level(self, timestamp)

    def save_data(self):
        save_start_time = time.time()
        
        # Save the collected data to a file with the timestamp
        file_name = f"results/data_{timestamp}.json"
        
        # Calculate file size before writing
        file_size_before = 0
        if os.path.exists(file_name):
            file_size_before = os.path.getsize(file_name)
        
        with open(file_name, 'w') as f:
            json.dump(self.url_data, f, indent=4)
        
        # Calculate file size after writing
        file_size_after = os.path.getsize(file_name) if os.path.exists(file_name) else 0
        
        save_duration = time.time() - save_start_time
        self.timing_logs["data_saving"] = {
            "start_time": save_start_time,
            "end_time": time.time(),
            "duration": save_duration,
            "file_name": file_name,
            "file_size_bytes": file_size_after,
            "file_size_mb": file_size_after / (1024 * 1024),
            "file_size_change": file_size_after - file_size_before,
            "description": "Saving collected data to JSON file",
            "urls_saved": len(self.url_data),
            "total_unique_ids": len(self.url_data)
        }

    def find_attributes(self, data):
        # Initialize an empty list to store all attributes
        all_attributes = []

        # Check if 'attributes' is in the dictionary
        if 'attributes' in data:
            # Extend the list with the keys of the 'attributes' dictionary and the associated unique_id
            for attribute, value in data['attributes'].items():
                all_attributes.append((attribute, data['unique_id'], value, data['text_size']))

        # Check if 'children' is in the dictionary
        if 'children' in data:
            # Iterate over the list of children
            for child in data['children']:
                # Recursively find attributes in the child
                all_attributes.extend(self.find_attributes(child))

        return all_attributes

    import json

    def get_combinations_by_level(self, level):
        # Initialize an empty list to store the combinations
        combinations = []

        # Iterate over the guids in the url_data dictionary
        for guid in self.url_data:
            # Iterate over the combinations_by_level list
            for combination in self.url_data[guid]['combinations_by_level']:
                print("combination['level']: ", combination['level'])
                # Check if the level of the current combination matches the given level
                if combination['level'] == str(level):
                    # If it does, flatten the combinations and extend the combinations list with them
                    flattened_combinations = [item for sublist in combination['combinations'] for item in sublist]
                    combinations.extend(flattened_combinations)

        # Return the combinations
        return combinations

    def computed_styles(self, level=1):
        level_start_time = time.time()
        
        # Get the combinations for the given level
        combinations = self.get_combinations_by_level(level)

        # Initialize an empty list to store all attributes
        all_attributes = []

        # Iterate over the outer dictionary
        for guid in self.url_data:
            # Find all attributes in the data
            all_attributes.extend(self.find_attributes(self.url_data[guid]['html_data']))

        # Convert the list to a pandas DataFrame to use nunique() and unique()
        attributes_df = pd.DataFrame(all_attributes, columns=['attribute', 'unique_id', 'value', 'text_size'])

        # Convert dictionaries in 'value' column to strings
        attributes_df['value'] = attributes_df['value'].apply(json.dumps)

        # Get total unique attributes
        total_unique_attributes = attributes_df['attribute'].nunique()

        # Get distinct values for each attribute
        distinct_values = attributes_df['attribute'].unique().tolist()

        # # Create a nested dictionary structure for each unique attribute and its values
        # attribute_values = {}
        # for attribute in distinct_values:
        #     attribute_df = attributes_df[attributes_df['attribute'] == attribute]
        #     attribute_values[attribute] = {}
        #     for value in attribute_df['value'].unique():
        #         print("value", value)
        #         # Convert value back to dictionary
        #         value_dict = json.loads(value)
        #         print("value_dict", value_dict)
        #         # Convert dictionary to a string representation
        #         value_str = json.dumps(value_dict)
        #         print("value_str", value_str)
        #         attribute_values[attribute][value_dict] = attribute_df[attribute_df['value'] == value]['unique_id'].tolist()

        # Create a nested list structure for each unique attribute and its values
        attribute_values = []
        for attribute in distinct_values:
            attribute_df = attributes_df[attributes_df['attribute'] == attribute]
            value_list = []
            text_size_value_list = []
            for value in attribute_df['value'].unique():
                value_str = value
                unique_ids = attribute_df[attribute_df['value'] == value]['unique_id'].tolist()
                # Filter the unique_ids by the combinations
                filtered_ids = [id for id in unique_ids if str(id) in combinations]
                value_list.append([value, filtered_ids])
                # value_list.append([value, unique_ids])
            for value in attribute_df['text_size'].unique():
                    value_str = str(value)  # Convert value to string
                    unique_ids = attribute_df[attribute_df['text_size'] == value]['unique_id'].tolist()
                    # Filter the unique_ids by the combinations
                    filtered_ids = [id for id in unique_ids if str(id) in combinations]
                    if filtered_ids:  # Append only if filtered_ids is not empty
                        text_size_value_list.append([value_str, filtered_ids])
            attribute_values.append([attribute, value_list, "text-size", text_size_value_list])
                
        # Define the directory path
        dir_path = f"results/computed_styles_level_{level}"
        # Check if the directory exists
        if not os.path.exists(dir_path):
            # If it doesn't exist, create it
            os.makedirs(dir_path)        
        # Save the output to a file
        computed_styles_file = f"{dir_path}/computed_styles_{timestamp}.json"
        with open(computed_styles_file, 'w') as f:
            json.dump({
                'total_unique_attributes': total_unique_attributes,
                'attribute_values': attribute_values
            }, f, indent=4)

        # Record timing for this level
        level_duration = time.time() - level_start_time
        self.timing_logs[f"computed_styles_level_{level}"] = {
            "start_time": level_start_time,
            "end_time": time.time(),
            "duration": level_duration,
            "level": level,
            "total_unique_attributes": total_unique_attributes,
            "distinct_attributes": len(distinct_values),
            "computed_styles_file": computed_styles_file,
            "file_size_bytes": os.path.getsize(computed_styles_file) if os.path.exists(computed_styles_file) else 0,
            "description": f"Generating computed styles for level {level}"
        }

        # Iterate over each attribute
        for attribute_data in attribute_values:
            attribute = attribute_data[0]
            values = attribute_data[1]

            # Create a new figure for each attribute
            # plt.figure(figsize=(10, 5))

            # Iterate over each value
            for value_data in values:
                value = value_data[0]
                ids = value_data[1]

                try:
                    # Use the length of the ids list as the y value
                    y = len(ids)

                    # Create a bar plot with the value as the x value and the length of the ids list as the y value
                    # plt.bar(value, y)

                except Exception as e:
                    # Write the error, attribute, value, and ids to the error file
                    # Open the error file
                    with open(f"results/computed_styles_images/error_log_{timestamp}.txt", 'w') as error_file:
                        error_file.write(f"Error: {str(e)}\n")
                        error_file.write(f"Attribute: {attribute}\n")
                        error_file.write(f"Value: {value}\n")
                        error_file.write(f"IDs: {ids}\n")
                        error_file.write("Traceback:\n")
                        error_file.write(traceback.format_exc())
                        error_file.write("\n\n")

        return total_unique_attributes, attribute_values, computed_styles_file

