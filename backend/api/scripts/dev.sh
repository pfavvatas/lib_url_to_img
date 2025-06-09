#!/bin/bash

# Navigate to the backend directory
cd ..

# Source the virtual environment
source venv/bin/activate

# Set PYTHONPATH to include the lib directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Navigate back to the api directory
cd api

# Execute the Python script
python3 main.py