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
        # Generate a unique timestamp for this instance
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
        self.timing_logs = {
            "start_time": time.time(),
            "url_processing": {},
            "total_urls": 0
        }

    def collect_data(self, urls, levels, driver, config):
        self.timing_logs["total_urls"] = len(urls)
        self.timing_logs["levels"] = levels
        self.url_timing_logs = {}  # Store detailed timing for each URL
        successful_urls = 0
        failed_urls = 0
        
        for i, url in enumerate(urls):
            url_start_time = time.time()
            unique_id = generate_unique_id()  # Generate a unique identifier            
            self.url_data[unique_id] = {'url': url, 'html_data': {}, 'combinations_by_level': {}}
            
            try:
                print(f"🌐 Processing URL {i+1}/{len(urls)}: {url}")
                
                # Process the URL with error handling
                url_timing_result = process_url(url, levels, driver, config, unique_id, self)
                
                # Check if processing was successful
                if url_timing_result is not None and not url_timing_result.get('error'):
                    successful_urls += 1
                    print(f"✅ Successfully processed URL {i+1}/{len(urls)}: {url}")
                else:
                    failed_urls += 1
                    print(f"⚠️  Failed to process URL {i+1}/{len(urls)}: {url} - {url_timing_result.get('error', 'Unknown error')}")
                    # Remove failed URL data to avoid inconsistencies
                    if not self.url_data[unique_id]['html_data']:
                        del self.url_data[unique_id]
                        
            except Exception as e:
                failed_urls += 1
                error_msg = f"Exception during URL processing: {str(e)}"
                print(f"❌ Error processing URL {i+1}/{len(urls)}: {url} - {error_msg}")
                
                # Log the error
                with open('url_processing_errors.log', 'a') as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - URL: {url} - Error: {error_msg}\n")
                    f.write(f"Traceback: {traceback.format_exc()}\n\n")
                
                # Create error timing result
                url_timing_result = {
                    "url": url,
                    "unique_id": unique_id,
                    "error": error_msg,
                    "exception": str(e),
                    "traceback": traceback.format_exc()
                }
                
                # Remove failed URL data to avoid inconsistencies
                if unique_id in self.url_data and not self.url_data[unique_id]['html_data']:
                    del self.url_data[unique_id]
            
            # Record timing for this URL (whether successful or failed)
            url_duration = time.time() - url_start_time
            self.timing_logs["url_processing"][f"url_{i+1}"] = {
                "url": url,
                "unique_id": unique_id,
                "start_time": url_start_time,
                "end_time": time.time(),
                "duration": url_duration,
                "description": f"Processing URL {i+1} of {len(urls)}",
                "detailed_timing": url_timing_result,  # Include the detailed timing from process_url
                "success": url_timing_result is not None and not (url_timing_result.get('error') if isinstance(url_timing_result, dict) else False)
            }
            
            print(f"⏱️  URL {i+1}/{len(urls)} completed in {url_duration:.2f}s")
            
        # Log final summary
        print(f"\n📊 Processing Summary:")
        print(f"✅ Successful URLs: {successful_urls}/{len(urls)}")
        print(f"❌ Failed URLs: {failed_urls}/{len(urls)}")
        print(f"📁 Total data records: {len(self.url_data)}")
        
        # Store summary in timing logs
        self.timing_logs["processing_summary"] = {
            "total_urls": len(urls),
            "successful_urls": successful_urls,
            "failed_urls": failed_urls,
            "success_rate": (successful_urls / len(urls)) * 100 if urls else 0,
            "final_data_records": len(self.url_data)
        }
            
        # create_image_by_level(self, self.timestamp)

    def save_data(self):
        save_start_time = time.time()
        
        # Save the collected data to a file with the timestamp
        file_name = f"results/data_{self.timestamp}.json"
        
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
        show_logs = False
        # Initialize an empty list to store the combinations
        combinations = []

        # Iterate over the guids in the url_data dictionary
        for guid in self.url_data:
            # Iterate over the combinations_by_level list
            for combination in self.url_data[guid]['combinations_by_level']:
                combo_start_time = time.time()
                # print("combination['level']: ", combination['level'])
                # Check if the level of the current combination matches the given level
                if combination['level'] == str(level):
                    # If it does, flatten the combinations and extend the combinations list with them
                    flattened_combinations = [item for sublist in combination['combinations'] for item in sublist]
                    combinations.extend(flattened_combinations)
                # Print duration for this combination processing
                show_logs and print(f"⏱ finished [ {guid} ] level {combination.get('level')} in {time.time() - combo_start_time:.4f}s")

        # Return the combinations
        return combinations

    def computed_styles(self, level=1):
        print(f"\033[94m=== Starting computed styles generation for level {level} in [computed_styles function] ===\033[0m")
        show_logs = False
        level_start_time = time.time()
        
        # Get the combinations for the given level
        show_logs and print(f"======================== Starting level {level} =========================")
        show_logs and print(f"⏱ starting level {level} in {time.time() - level_start_time:.4f}s")
        combinations = self.get_combinations_by_level(level)
        show_logs and print(f"⏱ finished level {level} in {time.time() - level_start_time:.4f}s")
        show_logs and print(f"======================== Finished level {level} =========================")
        

        # Initialize an empty list to store all attributes
        all_attributes = []

        # Iterate over the outer dictionary
        show_logs and print(f"======================== Starting find_attributes =========================")
        find_attributes_start_time = time.time()
        for guid in self.url_data:
            # Find all attributes in the data
            all_attributes.extend(self.find_attributes(self.url_data[guid]['html_data']))
            show_logs and print(f"⏱ finished [ {guid} ] find_attributes in {time.time() - find_attributes_start_time:.4f}s")
        show_logs and print(f"======================== Finished find_attributes =========================")

        # Convert the list to a pandas DataFrame to use nunique() and unique()
        show_logs and print(f"======================== Starting attributes_df =========================")
        attributes_df_start_time = time.time()
        attributes_df = pd.DataFrame(all_attributes, columns=['attribute', 'unique_id', 'value', 'text_size'])
        show_logs and print(f"⏱ finished attributes_df in {time.time() - attributes_df_start_time:.4f}s")
        show_logs and print(f"======================== Finished attributes_df =========================")

        # Convert dictionaries in 'value' column to strings
        show_logs and print(f"======================== Starting attributes_df_value =========================")
        attributes_df_value_start_time = time.time()
        attributes_df['value'] = attributes_df['value'].apply(json.dumps)
        show_logs and print(f"⏱ finished attributes_df_value in {time.time() - attributes_df_value_start_time:.4f}s")
        show_logs and print(f"======================== Finished attributes_df_value =========================")

        # Get total unique attributes
        show_logs and print(f"======================== Starting total_unique_attributes =========================")
        total_unique_attributes_start_time = time.time()
        total_unique_attributes = attributes_df['attribute'].nunique()
        show_logs and print(f"⏱ finished total_unique_attributes in {time.time() - total_unique_attributes_start_time:.4f}s")
        show_logs and print(f"======================== Finished total_unique_attributes =========================")

        # Get distinct values for each attribute
        show_logs and print(f"======================== Starting distinct_values =========================")
        distinct_values_start_time = time.time()
        distinct_values = attributes_df['attribute'].unique().tolist()
        show_logs and print(f"⏱ finished distinct_values in {time.time() - distinct_values_start_time:.4f}s")
        show_logs and print(f"======================== Finished distinct_values =========================")

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
        show_logs and print(f"======================== Starting attribute_values =========================")
        attribute_values_start_time = time.time()
        attribute_values = []

        # Vectorized precomputation and filtering by combinations
        vector_start_time = time.time()
        comb_set = set(combinations)
        # Precompute per-attribute unique lists (full, before filtering) for parity with previous behavior
        unique_values_by_attr = attributes_df.groupby('attribute')['value'].unique()
        unique_text_sizes_by_attr = attributes_df.groupby('attribute')['text_size'].unique()
        # Prepare filtered dataframe (only rows whose unique_id is in combinations)
        uid_str_start = time.time()
        attributes_df = attributes_df.copy()
        attributes_df['unique_id_str'] = attributes_df['unique_id'].astype(str)
        uid_str_duration = time.time() - uid_str_start
        filter_df_start = time.time()
        filtered_df = attributes_df[attributes_df['unique_id_str'].isin(comb_set)]
        filter_df_duration = time.time() - filter_df_start
        # Group once for values and text_size on the filtered set
        group_values_start = time.time()
        grouped_values = (
            filtered_df.groupby(['attribute', 'value'])['unique_id']
            .apply(list)
            .reset_index()
        )
        group_values_duration = time.time() - group_values_start
        group_text_start = time.time()
        grouped_text = (
            filtered_df.groupby(['attribute', 'text_size'])['unique_id']
            .apply(list)
            .reset_index()
        )
        group_text_duration = time.time() - group_text_start
        # Build fast lookup dictionaries
        build_dicts_start = time.time()
        values_lookup = {(row['attribute'], row['value']): row['unique_id'] for _, row in grouped_values.iterrows()}
        text_lookup = {(row['attribute'], row['text_size']): row['unique_id'] for _, row in grouped_text.iterrows()}
        build_dicts_duration = time.time() - build_dicts_start
        show_logs and print(
            f"⏱ vector prep: uid_str={uid_str_duration:.4f}s, filter={filter_df_duration:.4f}s, "
            f"group_values={group_values_duration:.4f}s, group_text={group_text_duration:.4f}s, build_dicts={build_dicts_duration:.4f}s"
        )

        show_logs and print(f"🔎 attribute_values: {len(distinct_values)} attributes to process (vectorized)")
        for attribute in distinct_values:
            per_attribute_start_time = time.time()
            value_list = []
            text_size_value_list = []

            # For 'value': include all unique values even if filtered ids are empty (parity with previous logic)
            values_unique = unique_values_by_attr.get(attribute, [])
            for value in values_unique:
                filtered_ids = values_lookup.get((attribute, value), [])
                value_list.append([value, filtered_ids])

            # For 'text_size': include only if filtered ids is not empty (parity with previous logic)
            # We can iterate directly over the filtered groups for this attribute
            # to avoid scanning all unique text sizes
            # Collect entries specific to this attribute
            # If needed, fall back to scanning unique list
            # Primary path: iterate filtered dict keys
            # Build from grouped_text rows for this attribute
            # Faster than per-value filtering
            # Note: values in text_lookup keys are raw (not str); convert to str when storing
            for (attr_key, text_size_key), ids in list(text_lookup.items()):
                if attr_key != attribute:
                    continue
                if ids:
                    text_size_value_list.append([str(text_size_key), ids])

            attribute_values.append([attribute, value_list, "text-size", text_size_value_list])
            show_logs and print(
                f"✅ attribute '{attribute}' built in {time.time() - per_attribute_start_time:.4f}s; values={len(value_list)}, text_sizes={len(text_size_value_list)}"
            )

        show_logs and print(f"⏱ finished attribute_values in {time.time() - attribute_values_start_time:.4f}s")
        show_logs and print(f"======================== Finished attribute_values =========================")

        show_logs and print(f"======================== Starting computed_styles_file =========================")
        computed_styles_file_start_time = time.time()
        # Define the directory path
        dir_path = f"results/computed_styles_level_{level}"
        # Check if the directory exists
        if not os.path.exists(dir_path):
            # If it doesn't exist, create it
            os.makedirs(dir_path)        
        # Save the output to a file
        computed_styles_file = f"{dir_path}/computed_styles_{self.timestamp}.json"
        with open(computed_styles_file, 'w') as f:
            json.dump({
                'total_unique_attributes': total_unique_attributes,
                'attribute_values': attribute_values
            }, f, indent=4)
        show_logs and print(f"⏱ finished computed_styles_file in {time.time() - computed_styles_file_start_time:.4f}s")
        show_logs and print(f"======================== Finished computed_styles_file =========================")

        # Record timing for this level
        show_logs and print(f"======================== Starting computed_styles_level_{level} =========================")
        computed_styles_level_start_time = time.time()
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
        show_logs and print(f"⏱ finished computed_styles_level_{level} in {time.time() - computed_styles_level_start_time:.4f}s")
        show_logs and print(f"======================== Finished computed_styles_level_{level} =========================")

        # Iterate over each attribute
        show_logs and print(f"======================== Starting computed_styles_images =========================")
        computed_styles_images_start_time = time.time()
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
                    with open(f"results/computed_styles_images/error_log_{self.timestamp}.txt", 'w') as error_file:
                        error_file.write(f"Error: {str(e)}\n")
                        error_file.write(f"Attribute: {attribute}\n")
                        error_file.write(f"Value: {value}\n")
                        error_file.write(f"IDs: {ids}\n")
                        error_file.write("Traceback:\n")
                        error_file.write(traceback.format_exc())
                        error_file.write("\n\n")
        show_logs and print(f"⏱ finished computed_styles_images in {time.time() - computed_styles_images_start_time:.4f}s")
        show_logs and print(f"======================== Finished computed_styles_images =========================")

        return total_unique_attributes, attribute_values, computed_styles_file

