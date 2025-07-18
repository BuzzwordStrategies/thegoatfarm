@echo off
title GOAT Farm Trading Platform

echo ========================================
echo    GOAT FARM TRADING PLATFORM v1.0
echo ========================================
echo.

:: Set Python path to include project root
set PYTHONPATH=%CD%;%PYTHONPATH%

:: Check for .env file
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env from env.example
    pause
    exit /b 1
)

:: Load environment variables from .env
echo Loading environment variables...
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%b"=="" (
        set "%%a=%%b"
    )
)

:: Try to start Redis (optional)
echo Checking for Redis...
where redis-server >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Starting Redis...
    start /B redis-server 2>nul
    timeout /t 2 >nul
) else (
    echo Redis not found - continuing without it
)

:: Start Python trading bots
echo.
echo Starting Trading Bots...
start /B python main.py

:: Wait a moment
timeout /t 3 >nul

:: Start Flask dashboard with proper path
echo Starting Flask Dashboard...
cd dashboard
start /B python app.py
cd ..

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
echo Trading Bots:
echo  - Bot 1: Trend-Following (BTC/ETH)
echo  - Bot 2: Mean-Reversion (SOL/ADA)
echo  - Bot 3: News-Driven (Multi-pair)
echo  - Bot 4: ML-Powered (Top 10)
echo.
echo Press Ctrl+C to stop all services
echo.

:: Keep window open
pause >nul
