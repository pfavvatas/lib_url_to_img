#!/bin/bash

# Create a virtual environment in the .venv directory
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies from requirements.txt
pip install -r requirements.txt