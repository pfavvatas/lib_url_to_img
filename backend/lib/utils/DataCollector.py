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

    def collect_data(self, urls, levels, driver, config):
        for url in urls:
            unique_id = generate_unique_id()  # Generate a unique identifier            
            self.url_data[unique_id] = {'url': url, 'html_data': {}, 'combinations_by_level': {}}
            process_url(url, levels, driver, config, unique_id, self)
            # create_image_by_level(self, timestamp)


    def save_data(self):
        

        # Save the collected data to a file with the timestamp
        file_name = f"results/data_{timestamp}.json"
        with open(file_name, 'w') as f:
            json.dump(self.url_data, f, indent=4)

    def find_attributes(self, data):
        # Initialize an empty list to store all attributes
        all_attributes = []

        # Check if 'attributes' is in the dictionary
        if 'attributes' in data:
            # Extend the list with the keys of the 'attributes' dictionary and the associated unique_id
            for attribute, value in data['attributes'].items():
                all_attributes.append((attribute, data['unique_id'], value))

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
        # Get the combinations for the given level
        combinations = self.get_combinations_by_level(level)

        # Initialize an empty list to store all attributes
        all_attributes = []

        # Iterate over the outer dictionary
        for guid in self.url_data:
            # Find all attributes in the data
            all_attributes.extend(self.find_attributes(self.url_data[guid]['html_data']))

        # Convert the list to a pandas DataFrame to use nunique() and unique()
        attributes_df = pd.DataFrame(all_attributes, columns=['attribute', 'unique_id', 'value'])

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
            for value in attribute_df['value'].unique():
                value_str = value
                unique_ids = attribute_df[attribute_df['value'] == value]['unique_id'].tolist()
                # Filter the unique_ids by the combinations
                filtered_ids = [id for id in unique_ids if str(id) in combinations]
                value_list.append([value, filtered_ids])
                # value_list.append([value, unique_ids])
            attribute_values.append([attribute, value_list])
                
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

            # Set the title of the plot to the attribute
            # plt.title(attribute)

            # Set the x and y labels
            # plt.xlabel('Value')
            # plt.ylabel('Number of IDs')

            # Show the plot
            # plt.show()

            # Define the directory path
            # dir_path = f"results/computed_styles_images/level_{level}"

            # Check if the directory exists
            # if not os.path.exists(dir_path):
            #     # If it doesn't exist, create it
            #     os.makedirs(dir_path)

            # Now you can safely save the plot to the directory
            # plt.savefig(f'{dir_path}/{attribute}_{timestamp}.png')

            # Close the plot
            # plt.close()

        return total_unique_attributes, attribute_values, computed_styles_file

