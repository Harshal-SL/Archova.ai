@echo off
echo ========================================
echo AI Architecture Engine - Quick Start
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install Gradio if needed
echo [1/3] Checking dependencies...
pip install gradio --quiet

REM Start FastAPI server in background
echo [2/3] Starting FastAPI server...
start "FastAPI Server" cmd /k "venv\Scripts\activate.bat && uvicorn app.main:app --reload"

REM Wait for server to start
echo Waiting for server to start...
timeout /t 5 /nobreak >nul

REM Start GUI demo
echo [3/3] Starting GUI demo...
echo.
echo ========================================
echo Server: http://localhost:8000
echo GUI Demo: http://localhost:7860
echo ========================================
echo.

python demo_gui.py

pause
