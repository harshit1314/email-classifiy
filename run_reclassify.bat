@echo off
echo ========================================
echo   Reclassifying Emails
echo ========================================
echo.

cd /d "%~dp0backend"
python reclassify_emails.py

echo.
pause
