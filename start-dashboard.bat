@echo off
echo Starting The GOAT Farm Dashboard...
echo =================================

echo Exporting environment variables...
call npm run export-env

if %errorlevel% neq 0 (
    echo Failed to export environment variables. Please check your Python environment.
    pause
    exit /b 1
)

echo.
echo Starting dashboard server...
call npm start 