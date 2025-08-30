@echo off
REM Link Dive AI Backend Server Startup Script for Windows
REM This script automatically clears ports and starts the backend server

echo ========================================
echo  Link Dive AI Backend Server Startup
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Starting Link Dive AI Backend Server...
echo.

REM Run the Python startup script
python start_server.py %*

if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start
    pause
    exit /b 1
)

echo.
echo Server stopped successfully
pause
