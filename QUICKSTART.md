# 🚀 lib_url_to_img - Quick Start Guide

A Python tool to convert website URLs into images by rendering the DOM HTML data with clustering capabilities.

## 📋 Prerequisites

- **Python 3.8+** (Required)
- **Node.js & npm** (Optional, for React frontend)
- **Chrome/Chromium browser** (Required for web scraping)
- **ChromeDriver** (See setup below)

## ⚡ Quick Start (One Command)

### Option 1: Pure Python Launcher (Recommended)
```bash
python run_project.py
```

### Option 2: Bash Script (Linux/Mac)
```bash
./run.sh
```

### Option 3: Windows Batch File
```cmd
run.bat
```

### Option 4: Original Multi-Process Runner
```bash
mprocs --config ./mprocs.yml
```

## 🔧 ChromeDriver Setup

This tool requires ChromeDriver to interact with Chrome browser:

1. Visit [ChromeDriver download page](https://chromedriver.chromium.org/downloads)
2. Download version matching your Chrome browser
3. Move to system PATH:
   ```bash
   # Linux/Mac
   sudo mv chromedriver /usr/local/bin/
   
   # Windows: Add to PATH or place in project folder
   ```

## 🏗️ Project Architecture

```
lib_url_to_img/
├── 🐍 backend/api/         # Flask API (Python) - Port 5000
├── 📁 backend/server/      # Static file server - Port 5005  
├── ⚛️  frontend/           # React UI - Port 3000
├── 🔧 backend/lib/         # Core Python library
└── 📊 clustering data/     # Various cluster ID files
```

## 🎯 What Each Service Does

| Service | Port | Purpose |
|---------|------|---------|
| **Flask API** | 5000 | URL processing, clustering API endpoints |
| **Static Server** | 5005 | Serves generated HTML files |
| **React Frontend** | 3000 | User interface for URL input and results |

## 🔗 Available Endpoints

After starting, visit:

- **📊 API Documentation**: http://localhost:5000/apidocs
- **🔧 API Endpoints**: http://localhost:5000
- **📁 Generated Files**: http://localhost:5005
- **⚛️ React Interface**: http://localhost:3000 (if Node.js available)

## 📡 API Usage

### Process URLs
```bash
curl -X POST http://localhost:5000/process-urls \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://google.com"],
    "levels": [1, 2, 3]
  }'
```

### Process Clusters
```bash
curl -X POST http://localhost:5000/process-clusters \
  -H "Content-Type: application/json" \
  -d '{
    "clusters": "[cluster_data_here]"
  }'
```

## 🐍 Python-Only Mode

If you only want the Python components (without React):

```bash
cd backend/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 🔧 Development Setup

### Manual Setup (All Components)

1. **Backend API Setup**:
   ```bash
   cd backend/api
   npm install scripty --save-dev
   npm run setup  # Creates venv and installs Python deps
   ```

2. **Backend Server Setup**:
   ```bash
   cd backend/server
   npm run setup  # Installs Node.js dependencies
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   ```

4. **Run All Services**:
   ```bash
   mprocs --config ./mprocs.yml
   ```

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver not found**:
   ```bash
   # Check if ChromeDriver is in PATH
   which chromedriver  # Linux/Mac
   where chromedriver  # Windows
   ```

2. **Port already in use**:
   - Kill processes using ports 3000, 5000, 5005
   - Or modify port in respective config files

3. **Python virtual environment issues**:
   ```bash
   # Remove and recreate
   cd backend/api
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Node.js/npm not found**:
   - Install from [nodejs.org](https://nodejs.org/)
   - Or use Python-only mode

### Environment Variables

```bash
# Optional configuration
export PORT=5000                    # Flask API port
export ENABLE_SWAGGER=true          # Enable API documentation
export PYTHONDONTWRITEBYTECODE=1    # Prevent .pyc files
```

## 📁 Output Files

The tool generates:

- **JSON data files**: `backend/api/results_*/data_*.json`
- **HTML visualization**: `backend/api/output_html_files/*.html`
- **Clustering results**: Various `cl_ids_*.txt` files
- **Images**: `backend/api/results/Images/`

## 🎨 Features

- ✅ **URL to Image conversion**
- ✅ **DOM structure analysis**
- ✅ **Machine learning clustering**
- ✅ **Interactive web interface**
- ✅ **RESTful API**
- ✅ **Swagger documentation**
- ✅ **Multi-level processing**

## 📝 Example Usage

1. Start the project: `python run_project.py`
2. Open browser to http://localhost:3000
3. Enter URLs to process
4. Select processing levels
5. View results and generated files

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Run tests: `cd backend/api && npm run tests`
4. Submit pull request

## 📄 License

See LICENSE file for details.

---

🎉 **Happy scraping and clustering!** 