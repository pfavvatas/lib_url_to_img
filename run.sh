#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting lib_url_to_img project..."
echo "======================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Setup Python virtual environment
echo "🔧 Setting up Python environment..."
cd backend/api

if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Go back to root directory
cd ../../

echo ""
echo "🎯 Starting services..."
echo "----------------------"

# Check if mprocs is available
if command -v mprocs &> /dev/null; then
    echo "🔄 Using mprocs to start all services..."
    mprocs --config ./mprocs.yml
else
    echo "⚠️  mprocs not found. Installing it..."
    if command -v npm &> /dev/null; then
        npm install -g mprocs
        echo "🔄 Starting services with mprocs..."
        mprocs --config ./mprocs.yml
    else
        echo "❌ npm not found. Cannot install mprocs."
        echo "   Please install Node.js/npm or use: python run_project.py"
        echo ""
        echo "🐍 Starting Python API only..."
        cd backend/api
        source .venv/bin/activate
        python main.py
    fi
fi 