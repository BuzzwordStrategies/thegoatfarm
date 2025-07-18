@echo off
title GOAT Farm Trading Platform

echo ========================================
echo    GOAT FARM TRADING PLATFORM v1.0
echo ========================================
echo.

:: Check for .env file
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env from env.example
    pause
    exit /b 1
)

:: Start Redis (if installed)
echo Starting Redis...
start /B redis-server 2>nul
timeout /t 2 >nul

:: Start Python trading bots
echo Starting Trading Bots...
start /B python main.py

:: Wait a moment
timeout /t 3 >nul

:: Start Flask dashboard
echo Starting Flask Dashboard...
start /B python dashboard\app.py

:: Wait a moment
timeout /t 3 >nul

:: Start Node.js dashboard
echo Starting Node.js Dashboard...
start /B node src\server\index.js

:: Wait for everything to start
timeout /t 5 >nul

echo.
echo ========================================
echo    GOAT FARM IS NOW RUNNING!
echo ========================================
echo.
echo Dashboards:
echo  - Flask: http://localhost:5000
echo  - Node.js: http://localhost:3001
echo.
echo Press Ctrl+C to stop all services
echo.

:: Keep window open
pause