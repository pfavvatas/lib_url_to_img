import json

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