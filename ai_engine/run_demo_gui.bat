@echo off
echo ========================================
echo AI Architecture Engine - GUI Demo
echo ========================================
echo.
echo Starting web interface...
echo Open your browser to: http://localhost:7860
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install Gradio if not already installed
pip install gradio --quiet

REM Run the GUI demo
python demo_gui.py

pause
