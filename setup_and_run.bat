@echo off
title AI-Powered Research Paper Intelligence System - Setup & Launcher
color 0A

echo ===========================================================================
echo    AI-POWERED RESEARCH PAPER INTELLIGENCE SYSTEM
echo    Automated One-Click Setup & Launch Script
echo ===========================================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo (Make sure to check "Add Python to PATH" during installation)
    echo.
    pause
    exit /b 1
)

:: 2. Create virtual environment if it does not exist
if not exist "venv" (
    echo [*] Creating Python Virtual Environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [*] Virtual environment found.
)

:: 3. Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

:: 4. Install / Update dependencies
echo [*] Installing all required libraries from requirements.txt...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies might have failed. Retrying...
    pip install -r requirements.txt
)
echo [OK] All dependencies are ready.

:: 5. Setup .env configuration file if missing
if not exist ".env" (
    echo [*] Generating .env configuration file from .env.example...
    copy .env.example .env >nul
    echo.
    echo ===========================================================================
    echo [IMPORTANT] .env file created!
    echo If your MySQL root user has a password, open .env in Notepad and set:
    echo DB_PASSWORD=your_password
    echo ===========================================================================
    echo.
)

:: 6. Test database connectivity & initialize tables
echo [*] Connecting to MySQL & verifying relational tables...
python tests/test_db_connection.py
if %errorlevel% neq 0 (
    color 0E
    echo.
    echo [NOTICE] If database connection failed:
    echo 1. Ensure MySQL Server is running (via MySQL Workbench, XAMPP, or Windows Service).
    echo 2. Ensure database 'research_paper_db' exists in MySQL:
    echo    CREATE DATABASE research_paper_db;
    echo 3. Check DB_PASSWORD in .env file.
    echo.
    pause
)

:: 7. Open Frontend in default browser
echo [*] Opening Frontend in your web browser...
start frontend/index.html

:: 8. Launch FastAPI Server
echo.
echo ===========================================================================
echo [SUCCESS] Starting FastAPI Backend at http://127.0.0.1:8000
echo Swagger API Documentation: http://127.0.0.1:8000/docs
echo Press Ctrl+C in this window to stop the server.
echo ===========================================================================
echo.

uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
