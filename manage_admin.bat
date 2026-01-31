@echo off
REM Manage Admin Account - Windows Batch Script
REM This script helps you manage the default admin account

echo.
echo ============================================================
echo   AI Email Classifier - Admin Account Manager
echo ============================================================
echo.

cd /d "%~dp0backend"

if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run the setup first.
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate

python manage_admin.py

pause
