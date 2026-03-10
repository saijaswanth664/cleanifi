@echo off
REM Simple launcher for the Data Cleaning App
REM This file ensures we're in the right directory

cd /d "%~dp0"

echo ========================================
echo   AI Data Cleaning Tool
echo ========================================
echo.
echo Starting application...
echo.

REM Use Python to run the Flask app
"C:\Users\saija\anaconda3\python.exe" flask_app.py

pause

