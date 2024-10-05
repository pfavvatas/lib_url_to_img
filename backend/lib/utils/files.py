import os
import json
from enum import Enum

class FileExtensions(Enum):
    JSON = '.json'
    TXT = '.txt'
    CSV = '.csv'
    PDF = '.pdf'
    PNG = '.png'
    JPEG = '.jpeg'
    MP4 = '.mp4'
    MP3 = '.mp3'
    DOCX = '.docx'

class FileNames(Enum):
    DATA = 'Data'
    COMBINATIONS = 'Combinations'
    COMBINATIONS_BY_LEVEL = 'CombinationsByLevel'
    COMBINATIONS_TAGS_BY_UNIQUE_ID = 'CombinationsTags'
    TAGS_CONFIGURATION = 'configuration/tags'

def writeToFile(folder_name, file_name, file_extension, data):
    os.makedirs(folder_name, exist_ok=True)
    with open(os.path.join(folder_name, ''.join([file_name, file_extension])), 'w') as f:
        json.dump(data, f, indent=4)