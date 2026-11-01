@echo off
REM VitaVerse - Model Training Pipeline
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"

echo ===================================================
echo  VitaVerse - Model Training Pipeline
echo ===================================================
echo Working directory: %CD%
echo.

python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [1/2] Generating reproducible demonstration dataset...
python ml/generate_demo_data.py --samples 2400
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to generate demonstration data.
    pause
    exit /b 1
)

echo.
echo [2/2] Training Scikit-learn comfort classification model...
python ml/train_model.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to train comfort model.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Model training and evaluation complete!
echo Artifacts saved:
echo   - ml/comfort_model.joblib
echo   - ml/model_metadata.json
echo.
pause
