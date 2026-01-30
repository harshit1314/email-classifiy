@echo off
REM Quick setup script for Windows - Sets Kaggle token and starts training

echo ========================================
echo   AI Email Classifier Training Setup
echo ========================================
echo.

REM Set your Kaggle API token
set KAGGLE_API_TOKEN=KGAT_cab1dfcf153550d2962a37b1ab848e87

echo [OK] Kaggle API token configured
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if kagglehub is installed
python -c "import kagglehub" >nul 2>&1
if errorlevel 1 (
    echo Installing kagglehub...
    pip install kagglehub
    echo [OK] kagglehub installed
) else (
    echo [OK] kagglehub already installed
)

echo.
echo ========================================
echo   Starting Training...
echo ========================================
echo.
echo This will:
echo   1. Download Enron dataset (5,000 emails)
echo   2. Auto-label emails by category
echo   3. Train improved classifier
echo   4. Show accuracy results
echo   5. Save trained model
echo.
pause

REM Run training
python train_with_enron.py

echo.
echo ========================================
echo   Training Complete!
echo ========================================
echo.
pause
