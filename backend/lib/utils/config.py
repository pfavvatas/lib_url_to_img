import json
import os
tags_path = os.path.join(os.path.dirname(__file__), '../configuration/tags.json')

class Config:
    def __init__(self, filename):
        with open(filename) as f:
            data = json.load(f)

        for key, value in data.items():
            setattr(self, key, value)

    def get_attribute(self, attr, default=None):
        attributes = attr.split('.')
        result = self
        for attribute in attributes:
            if isinstance(result, dict):
                result = result.get(attribute, default)
            else:
                result = getattr(result, attribute, default)
            if result is default:
                break
        return result

    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

# Function to get tag order from JSON file
def get_tag_order():
    with open(tags_path, "r") as file:
        tag_data = json.load(file)
    return tag_data["tag_order"]
def get_tag_colors():
    with open(tags_path, "r") as file:
        tag_data = json.load(file)
    return tag_data["tag_colors"]