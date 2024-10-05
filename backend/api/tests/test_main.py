# FILE: tests/test_main.py

import unittest
import json
import sys
import os
from functools import wraps

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

# List of test methods to run
tests_to_run = [
    "test_process_urls"
    ]

def run_only_tests(tests):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if func.__name__ not in tests:
                raise unittest.SkipTest(f"Skipping {func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

class MainTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @run_only_tests(tests_to_run)
    def test_process_urls(self):
        print("\nRunning test_process_urls")
        
        # Define the payload
        payload = {
            "urls": ["http://example.com", "http://test.com"]
        }

        # Send POST request to /process-urls
        response = self.app.post('/process-urls', 
                                 data=json.dumps(payload), 
                                 content_type='application/json')

        # Check the status code
        self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")

        # Check the response data
        response_data = json.loads(response.data)
        expected_data = {
            "http://example.com": "Processed data for http://example.com",
            "http://test.com": "Processed data for http://test.com"
        }
        self.assertEqual(response_data, expected_data, f"Expected response data {expected_data}, got {response_data}")

        # Additional checks
        self.assertIsInstance(response_data, dict, f"Expected response data to be a dictionary, got {type(response_data)}")
        self.assertTrue("http://example.com" in response_data, "Expected 'http://example.com' in response data")
        self.assertTrue("http://test.com" in response_data, "Expected 'http://test.com' in response data")

        # Print additional information
        print("Response status code:", response.status_code)
        print("Response data:", response_data)

    @run_only_tests(tests_to_run)
    def test_invalid_urls(self):
        print("\nRunning test_invalid_urls")
        
        # Define the payload with invalid URLs
        payload = {
            "urls": ["invalid-url", "another-invalid-url"]
        }

        # Send POST request to /process-urls
        response = self.app.post('/process-urls', 
                                 data=json.dumps(payload), 
                                 content_type='application/json')

        # Check the status code
        self.assertEqual(response.status_code, 400, f"Expected status code 400, got {response.status_code}")

        # Check the response data
        response_data = json.loads(response.data)
        expected_data = {
            "error": "Invalid URLs provided"
        }
        self.assertEqual(response_data, expected_data, f"Expected response data {expected_data}, got {response_data}")

        # Additional checks
        self.assertIsInstance(response_data, dict, f"Expected response data to be a dictionary, got {type(response_data)}")
        self.assertTrue("error" in response_data, "Expected 'error' in response data")

        # Print additional information
        print("Response status code:", response.status_code)
        print("Response data:", response_data)

if __name__ == '__main__':
    unittest.main()