@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting lib_url_to_img project...
echo ======================================

REM Check if Python 3 is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed.
    pause
    exit /b 1
)

REM Setup Python virtual environment
echo 🔧 Setting up Python environment...
cd backend\api

if not exist ".venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call .venv\Scripts\activate

REM Install Python dependencies
echo 📥 Installing Python dependencies...
pip install -r requirements.txt

REM Go back to root directory
cd ..\..

echo.
echo 🎯 Starting services...
echo ----------------------

REM Check if mprocs is available
mprocs --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  mprocs not found. Checking for npm...
    npm --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ npm not found. Cannot install mprocs.
        echo    Please install Node.js/npm or use: python run_project.py
        echo.
        echo 🐍 Starting Python API only...
        cd backend\api
        call .venv\Scripts\activate
        python main.py
        pause
    ) else (
        echo 📥 Installing mprocs...
        npm install -g mprocs
        echo 🔄 Starting services with mprocs...
        mprocs --config .\mprocs.yml
    )
) else (
    echo 🔄 Using mprocs to start all services...
    mprocs --config .\mprocs.yml
)

pause 