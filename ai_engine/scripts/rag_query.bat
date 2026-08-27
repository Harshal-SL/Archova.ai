@echo off
:: Launcher for scripts/rag_query.py — always uses the project venv
:: Run from project root so all imports resolve correctly
set TRANSFORMERS_VERBOSITY=error
set HF_HUB_VERBOSITY=warning
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" -W ignore "%~dp0scripts\rag_query.py" %*
