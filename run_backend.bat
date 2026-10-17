@echo off
REM VitaVerse - Local Python FastAPI Backend Launcher
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"

echo ===================================================
echo  VitaVerse - Local Python FastAPI Backend
echo ===================================================
echo Working directory: %CD%
echo.

python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

if not exist "ml\comfort_model.joblib" (
    echo [WARNING] Model file ml\comfort_model.joblib not found.
    echo Training model first...
    call train_model.bat
)

echo Starting FastAPI server on http://127.0.0.1:8000 ...
echo - API Documentation: http://127.0.0.1:8000/docs
echo - Interactive Demo:  http://127.0.0.1:8000/demo
echo.
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
