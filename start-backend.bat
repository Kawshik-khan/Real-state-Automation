@echo off
title Grandeur Living - Real Estate Automation Backend
echo =======================================================
echo Starting FastAPI Backend for AI Evaluation Engine
echo =======================================================
cd /d "%~dp0"
if exist "backend\.venv\Scripts\activate.bat" (
    echo Activating backend virtual environment...
    call backend\.venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] virtual environment not found. Using system python...
)
set PYTHONPATH=%~dp0backend
echo Starting uvicorn on http://127.0.0.1:8000 ...
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
pause
