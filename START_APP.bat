@echo off
REM Simple launcher for the Data Cleaning App
REM This file ensures we're in the right directory

cd /d "C:\Users\DELL\Desktop\data analyst"

echo ========================================
echo   AI Data Cleaning Tool
echo ========================================
echo.
echo Starting application...
echo.

REM Use Python to run the Flask app
python flask_app.py

pause

