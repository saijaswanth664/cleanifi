@echo off
echo Installing required packages...
echo.
cd /d "%~dp0"

REM Try to find Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python -m pip install -r requirements.txt
) else (
    REM Try Python3
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        python3 -m pip install -r requirements.txt
    ) else (
        REM Use the found Anaconda path
        "C:\Users\saija\anaconda3\python.exe" -m pip install -r requirements.txt
    )
)
echo.
echo Installation complete!
echo You can now run the application using run_app.bat
pause

