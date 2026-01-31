#!/bin/bash
# Manage Admin Account - Shell Script
# This script helps you manage the default admin account

echo ""
echo "============================================================"
echo "  AI Email Classifier - Admin Account Manager"
echo "============================================================"
echo ""

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run the setup first."
    echo ""
    exit 1
fi

source venv/bin/activate

python manage_admin.py
