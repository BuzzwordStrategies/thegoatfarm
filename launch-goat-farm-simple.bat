@echo off
title GOAT Farm Trading Platform

echo ========================================
echo    GOAT FARM TRADING PLATFORM v1.0
echo ========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

:: Check for .env file
if not exist .env (
    echo ERROR: .env file not found!
    echo Please run: python scripts/fix-goat-farm.py
    pause
    exit /b 1
)

:: Install requirements if needed
echo Checking dependencies...
pip install -r requirements.txt >nul 2>&1

:: Start the main application
echo.
echo Starting The GOAT Farm...
echo.
python main.py

pause
