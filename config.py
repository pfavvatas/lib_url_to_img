import json

class Config:
    def __init__(self, filename):
        with open(filename) as f:
            data = json.load(f)

        for key, value in data.items():
            setattr(self, key, value)

    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())