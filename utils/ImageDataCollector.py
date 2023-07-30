import datetime
import json
import os
from utils.image import create_image_for_level

# Generate a timestamp for the file name
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

class ImageDataCollector:
    def __init__(self, url_data):
        self.levels_info = self.process_url_data(url_data)

    def process_url_data(self, url_data):
        levels_info = {}
        for url_id, url_info in url_data.items():
            combinations_by_level = url_info.get('combinations_by_level', [])
            for level_data in combinations_by_level:
                level = level_data['level']
                urls_info = level_data['image_data']
                text_size_sum = sum(item['text_size'] for item in urls_info)  # Calculate the sum of text_size for this urls_info
                if level not in levels_info:
                    levels_info[level] = {'max_text_size': text_size_sum, 'urls_info': []}
                levels_info[level]['urls_info'].append({'text_size_sum' : text_size_sum, 'url': url_info['url'], 'image_data': urls_info})

        # After processing all url_data, find the maximum sum of text_size for each level
        for level_data in levels_info.values():
            max_text_sizes = [sum(item['text_size'] for item in item['image_data']) for item in level_data['urls_info']]
            level_data['max_text_size'] = max(max_text_sizes)

        return levels_info

    def save_to_json(self, file_path):
        # Save the collected data to a file with the timestamp
        file_name = f"results/image_data_{timestamp}.json"
        with open(file_name, 'w') as f:
            json.dump(self.levels_info, f, indent=4)

    def generate_images(self):
        # Create the 'Images' folder if it doesn't exist
        os.makedirs("results/Images", exist_ok=True)

        # Loop through the levels and create images for each level
        prev_image = None
        for level, level_data in self.levels_info.items():
            max_text_size = level_data['max_text_size']
            urls_info = level_data['urls_info']

            print("========================")
            print("level: " ,level)
            level_image = create_image_for_level(urls_info, max_text_size, prev_image)

            # Save the image with the level number and timestamp
            level_image.save(f"results/images/{level}_{timestamp}.png")

            prev_image = level_image.copy()
