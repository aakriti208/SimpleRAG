@echo off
REM SimpleRAG Installation Script for Windows
REM This script automates the installation of SimpleRAG for Canvas LMS

echo ==========================================
echo SimpleRAG Installation Script
echo ==========================================
echo.

REM Check for Python
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python found: %PYTHON_VERSION%

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist "venv" (
    echo [INFO] Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)
python -m venv venv
echo [SUCCESS] Virtual environment created

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo [SUCCESS] Pip upgraded

REM Install requirements
echo [INFO] Installing Python dependencies (this may take a few minutes)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Python dependencies installed

REM Setup environment file
echo [INFO] Setting up environment configuration...
if not exist ".env" (
    copy .env.template .env >nul
    echo [SUCCESS] Created .env file from template
    echo [INFO] Please edit .env file with your Canvas API credentials
) else (
    echo [INFO] .env file already exists (skipping)
)

REM Check for Ollama
echo [INFO] Checking for Ollama installation...
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Ollama is installed

    REM Check if model is installed
    echo [INFO] Checking for gemma:2b model...
    ollama list | findstr /C:"gemma:2b" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] Installing gemma:2b model (this will take a few minutes)...
        ollama pull gemma:2b
        echo [SUCCESS] gemma:2b model installed
    ) else (
        echo [SUCCESS] gemma:2b model is installed
    )
) else (
    echo [ERROR] Ollama is not installed
    echo.
    echo Ollama is required for answer generation.
    echo Installation instructions:
    echo   1. Visit https://ollama.ai
    echo   2. Download and install Ollama for Windows
    echo   3. Run: ollama serve
    echo   4. Run: ollama pull gemma:2b
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\metadata" mkdir data\metadata
echo [SUCCESS] Directories created

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Next steps:
echo.
echo 1. Configure your Canvas API credentials:
echo    Edit the .env file with your Canvas API token and course IDs
echo.
echo 2. Activate the virtual environment (in new terminal sessions):
echo    venv\Scripts\activate.bat
echo.
echo 3. Ingest your Canvas content:
echo    python scripts\ingest_data.py --course YOUR_COURSE_ID --full
echo.
echo 4. Start the web interface:
echo    python app.py
echo    Then visit: http://localhost:8000
echo.
echo For help, see README.md or contact STEM CLEAR support
echo.
pause
