import re
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import random

class HTMLTag:
    def __init__(self, webelement, driver, depth=0, parent_id=None):
        self.unique_id = id(self)
        self.parent_id = parent_id  # Save the parent's unique_id
        self.tag_name = webelement.tag_name
        self.attributes = self.get_all_attributes(webelement, driver)  
        self.depth = depth
        self.text = self.clean_text(webelement.text.strip()) if webelement.text else ""
        self.text_size = self.count_text()

        # We only create children list and recursively populate it if the current webelement has child elements.
        if webelement.find_elements(By.XPATH, ".//*"):
            self.children = [HTMLTag(child, driver, depth=depth+1, parent_id=self.unique_id) for child in webelement.find_elements(By.XPATH, "./*")]
        else:
            self.children = []

    def get_all_attributes(self, webelement, driver):
        attrs = driver.execute_script("""
        let elem = arguments[0], 
            attrs = {};
        for(let i = 0; i < elem.attributes.length; i++) {
            attrs[elem.attributes[i].name] = elem.attributes[i].value;
        }
        return attrs;
        """, webelement)
        css_props = driver.execute_script("""
        let elem = arguments[0], 
            computedStyle = window.getComputedStyle(elem),
            cssProps = {};
        for(let i = 0; i < computedStyle.length; i++) {
            let prop = computedStyle[i];
            cssProps[prop] = computedStyle.getPropertyValue(prop);
        }
        return cssProps;
        """, webelement)
        rect = driver.execute_script('return arguments[0].getBoundingClientRect()', webelement)
        css_props.update(rect)
        attrs = {**attrs, **css_props}
        return attrs
    
    def to_dict(self):
        return {
            'unique_id': self.unique_id,
            'parent_id': self.parent_id,
            'tag_name': self.tag_name,
            'text': self.text,
            'text_size': self.text_size,
            'attributes': self.attributes,
            'children': [child.to_dict() for child in self.children],
            'depth': self.depth
        }

    def clean_text(self, text):
        # Remove non-printable ASCII characters
        return re.sub(r'[^\x20-\x7E]', ' ', text)
    
    def remove_special_chars(self, text):
        # Define a regular expression pattern to match special characters
        pattern = r'[^\w\s]+'
        # Replace special characters with spaces
        return re.sub(pattern, ' ', text)

    def count_text(self):
        # Remove HTML tags and special characters
        # clean_text = re.sub('<.*?>', '', self.text)  # Remove HTML tags
        clean_text = re.sub(r'[^\w\s]', '', self.text)  # Remove special characters

        # Count the number of words
        word_count = len(re.findall(r'\w+', clean_text))
        return word_count

    def print_tree(self, indent="  "):
        print(self.depth * indent + self.tag_name, self.unique_id)
        for attr, value in self.attributes.items():
            print(self.depth * indent + " " + attr, value)
        for child in self.children:
            child.print_tree(indent)

    def find_tag_name_by_id(self, unique_id):
        # Check if the current node is the one we're looking for
        if str(self.unique_id) == str(unique_id):
            return self.tag_name

        # If it's not, look in each of the node's children
        for child in self.children:
            result = child.find_tag_name_by_id(unique_id)
            if result is not None:
                return result

        # If the node wasn't found in this branch of the tree, return None
        return None
    
    def find_node_by_id(self, unique_id):
        if str(self.unique_id) == str(unique_id):
            return self

        for child in self.children:
            result = child.find_node_by_id(unique_id)
            if result:
                return result

        return None

    def find_subchildren_by_id(self, unique_id):
        # Check if the current node is the one we're looking for
        if str(self.unique_id) == str(unique_id):
            return self.children

        # If it's not, recursively search in each of the node's children
        for child in self.children:
            result = child.find_subchildren_by_id(unique_id)
            if result is not None:
                return result

        # If the node wasn't found in this branch of the tree, return None
        return None
    
    def find_subchildren_unique_ids_by_id(self, unique_id):
        # Check if the current node is the one we're looking for
        if str(self.unique_id) == str(unique_id):
            # Return a list containing the unique IDs of all the children
            return [child.unique_id for child in self.children]

        # If it's not, recursively search in each of the node's children
        for child in self.children:
            result = child.find_subchildren_unique_ids_by_id(unique_id)
            if result:
                # If the result is not an empty list, it means the unique_id was found in this branch
                return result

        # If the node wasn't found in this branch of the tree, return an empty list
        return []
    
    def calculate_subchildren_text_sizes(self, node, your_list_of_ids, subchildren_unique_ids):
        # Convert the elements in your_list_of_ids to integers
        your_list_of_ids_int = [int(id_str) for id_str in your_list_of_ids]

        if not node.children:
            # If the node has no children, simply return its own text_size
            return node.text_size

        # Calculate the sum of text_sizes for all subchildren except those in your_list_of_ids_int
        total_subchildren_text_size = 0
        for subchild_id in subchildren_unique_ids:
            if subchild_id not in your_list_of_ids_int:
                subchild_node = self.find_node_by_id(subchild_id)
                if subchild_node:
                    total_subchildren_text_size += subchild_node.text_size
        

        # Subtract the sum from the node's own text_size to get the updated text_size
        updated_text_size = node.text_size - total_subchildren_text_size

        return updated_text_size

    def get_width_and_height(self):
        attributes = self.attributes
        width = attributes.get('width', None)
        height = attributes.get('height', None)
        return width, height
    
    def random_color(self):
        r = lambda: random.randint(0,255)
        return '#%02X%02X%02X' % (r(),r(),r())

    def generate_tag_color_map(self, combination_list, existing_map_file):
        # Load the existing map if any
        try:
            with open(existing_map_file, 'r') as f:
                color_map = json.load(f)
        except FileNotFoundError:
            color_map = {"tag_colors": {}}

        for combination in combination_list:
            # Convert ids to tag names
            tag_names = [self.find_tag_name_by_id(id) for id in combination]
            tag_key = ",".join(tag_names)

            # Add to map if not already present
            if tag_key not in color_map["tag_colors"]:
                color_map["tag_colors"][tag_key] = self.random_color()

        # Save the updated map
        with open(existing_map_file, 'w') as f:
            json.dump(color_map, f, indent=4)
