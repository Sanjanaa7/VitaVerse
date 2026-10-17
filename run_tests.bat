@echo off
REM VitaVerse - Automated Test Runner
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"

echo ===================================================
echo  VitaVerse - Automated Test Runner
echo ===================================================
echo Working directory: %CD%
echo.
python -m pytest tests/ -v
pause
