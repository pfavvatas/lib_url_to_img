#!/bin/bash

# Navigate to the virtual environment directory
cd .venv

# Source the virtual environment
source bin/activate

# Navigate back to the project root
cd ..

# Navigate to the tests folder
cd tests

# Run the unittests
python -m unittest discover