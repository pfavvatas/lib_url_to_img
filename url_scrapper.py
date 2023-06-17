from selenium import webdriver
from selenium.webdriver.common.by import By

class HTMLTag:
    def __init__(self, webelement, driver, depth=0):
        self.unique_id = id(self)
        self.tag_name = webelement.tag_name
        self.attributes = self.get_all_attributes(webelement, driver)  
        self.depth = depth

        # We only create children list and recursively populate it if the current webelement has child elements.
        if webelement.find_elements(By.XPATH, ".//*"):
            self.children = [HTMLTag(child, driver, depth=depth+1) for child in webelement.find_elements(By.XPATH, "./*")]
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
            'tag_name': self.tag_name,
            'attributes': self.attributes,
            'children': [child.to_dict() for child in self.children],
            'depth': self.depth
        }



    def print_tree(self, indent="  "):
        print(self.depth * indent + self.tag_name, self.unique_id)
        for attr, value in self.attributes.items():
            print(self.depth * indent + " " + attr, value)
        for child in self.children:
            child.print_tree(indent)
