import os
import json
from PIL import Image, ImageDraw
from .config import *
tags_path = os.path.join(os.path.dirname(__file__), '../configuration/tags.json')

def get_tag_color(keys):
    with open(tags_path, 'r') as file:
        data = json.load(file)
        
    tag_colors = data['tag_colors']
    
    if keys in tag_colors:
        return tag_colors[keys]
    else:
        return None

def create_image_for_level(level_data, max_text_size, prev_image=None):
    # # Calculate the total height for the image based on the number of urls_info rows
    # num_rows = len(level_data)
    # total_height = num_rows  # You can adjust this value as needed for spacing between rows

    # level_image = Image.new('RGB', (max_text_size, total_height), color='white')
    # draw = ImageDraw.Draw(level_image)

    # y_offset = 0  # Starting y offset at 0
    # if prev_image:
    #     level_image.paste(prev_image, (0, 0))

    # for urls_info in level_data:
    #     row_width = sum(item['text_size'] for item in urls_info['image_data'])
    #     if row_width < max_text_size:
    #         factor = max_text_size / row_width
    #         text_sizes = [int(size * factor) for size in [item['text_size'] for item in urls_info['image_data']]]
    #     else:
    #         text_sizes = [item['text_size'] for item in urls_info['image_data']]

    #     x_offset = 0  # Starting x offset at 0 for each row
    #     for i, text_size in enumerate(text_sizes):
    #         color = urls_info['image_data'][i]['color']
    #         draw.rectangle([x_offset, y_offset, x_offset + text_size, y_offset + 1], fill=color)
    #         x_offset += text_size

    #     y_offset += 1  # Move the y offset to the next row

    # return level_image

    #try2
    target_width = 1080  # You can adjust this value as needed

    # Calculate the scaling factor based on the maximum text size and target width
    scale_factor = min(1.0, target_width / max_text_size)

    # Calculate the total height for the image based on the number of urls_info rows
    num_rows = len(level_data)
    total_height = num_rows  # You can adjust this value as needed for spacing between rows

    # Scale the max_text_size based on the scaling factor
    scaled_max_text_size = int(max_text_size * scale_factor)

    level_image = Image.new('RGB', (scaled_max_text_size, total_height), color='white')
    draw = ImageDraw.Draw(level_image)

    y_offset = 0  # Starting y offset at 0
    if prev_image:
        prev_width, prev_height = prev_image.size
        prev_image = prev_image.resize((scaled_max_text_size, prev_height))
        level_image.paste(prev_image, (0, 0))

    for urls_info in level_data:
        row_width = sum(item['text_size'] for item in urls_info['image_data'])
        scaled_row_width = max(1, int(row_width * scale_factor))  # Ensure scaled_row_width is at least 1
        if scaled_row_width < scaled_max_text_size:
            factor = scaled_max_text_size / scaled_row_width
            text_sizes = [int(size * factor) for size in [item['text_size'] for item in urls_info['image_data']]]
        else:
            text_sizes = [int(size * scale_factor) for size in [item['text_size'] for item in urls_info['image_data']]]

        x_offset = 0  # Starting x offset at 0 for each row
        for i, text_size in enumerate(text_sizes):
            color = urls_info['image_data'][i]['color']
            draw.rectangle([x_offset, y_offset, x_offset + text_size, y_offset + 1], fill=color)
            x_offset += text_size

        y_offset += 1  # Move the y offset to the next row

    return level_image

    
def generate_image_data(combinations_by_level, root):
     for item in combinations_by_level:
        combinations_keys_ordered = item['combinations_keys_ordered']
        image_data = []
        encountered_ids = set()  # Set to store encountered ids

        for combination in combinations_keys_ordered:
            keys = combination[0]  # Get the keys
            ids = combination[1]  # Get the corresponding ids
            last_id = ids[-1]  # Get the last id
            new_id = '-'.join(ids)

            if new_id in encountered_ids:
                continue  # Skip appending duplicate object
            
            for id in new_id.split('-'):
                subchildren_unique_ids_list = root.find_subchildren_unique_ids_by_id(id)

            node = root.find_node_by_id(last_id)
            if node is not None:
                width, height = node.get_width_and_height()
                key_data = {
                    'id': new_id, 
                    'keys': keys, 
                    'color': get_tag_color(keys),
                    'text_size': node.calculate_subchildren_text_sizes(node,ids,subchildren_unique_ids_list),
                    'width': width, 
                    'height': height
                    }
                image_data.append(key_data)
                encountered_ids.add(last_id)  # Add id to set
                
        item['image_data'] = image_data

def create_image_by_level(data, timestamp):
    # max_image_width = 1920
    # tag_order = get_tag_order()
    # tag_colors = get_tag_colors()

    # # Create and combine images
    # final_image_height = 0
    # final_image = Image.new("RGB", (1920, 1), "white")

    # # Save the final image
    # output_path = f"results/final_image{timestamp}.png"
    # final_path = output_path
    # final_image.save(final_path)

    # Create the 'Images' folder if it doesn't exist
    os.makedirs("results/Images", exist_ok=True)

    # Loop through the data and create images for each level
    prev_image = None
    for key, value in data.items():
        max_text_size = value['max_text_size']
        urls_info = value['urls_info']

        level_image = create_image_for_level(urls_info, max_text_size, prev_image)

        # Save the image with the level number and timestamp
        timestamp = "your_timestamp_here"  # Replace this with the actual timestamp
        level_image.save(f"results/Images/{key}_{timestamp}.png")

        prev_image = level_image.copy()

def create_image(data, folder_name):
    max_image_width = 1920
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
            width = 0#int(image_data["width"]/1920)
            height = 0#int(image_data["height"])

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