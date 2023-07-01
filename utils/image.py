import os
import json
from PIL import Image
from .config import *

def get_tag_color(keys):
    with open('configuration/tags.json', 'r') as file:
        data = json.load(file)
        
    tag_colors = data['tag_colors']
    
    if keys in tag_colors:
        return tag_colors[keys]
    else:
        return None
    
def generate_image_data(combinations_by_level, root):
     for item in combinations_by_level:
        combinations_keys_ordered = item['combinations_keys_ordered']
        image_data = []
        for combination in combinations_keys_ordered:
            keys = combination[0]  # Get the keys
            ids = combination[1]  # Get the corresponding ids
            last_id = ids[-1]  # Get the last id

            node = root.find_node_by_id(last_id)
            if node is not None:
                width, height = node.get_width_and_height()
                key_data = {
                    'id': last_id, 
                    'keys': keys, 
                    'color': get_tag_color(keys),
                    'width': width, 
                    'height': height
                    }
                image_data.append(key_data)
        item['image_data'] = image_data

def create_image(data, folder_name):
    max_image_width = 20
    tag_order = get_tag_order()
    tag_colors = get_tag_colors()

    # Create and combine images
    final_image_height = 0
    final_image = Image.new("RGB", (max_image_width, 0), "white")

    for level_data in data:
        images = []
        for combination_key, image_ids in level_data["combinations_keys_ordered"]:
            for image_data in level_data["image_data"]:
                if image_data["id"] in image_ids:
                    images.append(image_data)

        images.sort(key=lambda x: tag_order[x["keys"]])

        level_image_width = 0
        level_image_height = 1  # Set initial height to 1 pixel
        level_images = []

        for image_data in images:
            color = tag_colors[image_data["keys"]]
            width = int(image_data["width"]/200)
            height = int(image_data["height"])

            level_image_width += width
            # level_image_height = max(level_image_height, height)

            img = Image.new("RGB", (width, height), color)
            level_images.append(img)

        level_image = Image.new("RGB", (level_image_width, level_image_height),"white")

        x_offset = 0
        for img in level_images:
            level_image.paste(img, (x_offset, 0))
            x_offset += img.width

        final_image_height += level_image_height
        final_image = final_image.crop((0, 0, max_image_width, final_image_height))
        final_image.paste(level_image, (0, final_image_height - level_image_height))

    # Save the final image
    output_path = "final_image.png"
    final_path = os.path.join(folder_name, output_path)
    final_image.save(final_path)