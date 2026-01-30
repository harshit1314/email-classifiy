#!/bin/bash
# Quick setup script for Mac/Linux - Sets Kaggle token and starts training

echo "========================================"
echo "  AI Email Classifier Training Setup"
echo "========================================"
echo

# Set your Kaggle API token
export KAGGLE_API_TOKEN=KGAT_cab1dfcf153550d2962a37b1ab848e87

echo "[OK] Kaggle API token configured"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python first."
    exit 1
fi

echo "[OK] Python found"
echo

# Check if kagglehub is installed
if ! python3 -c "import kagglehub" &> /dev/null; then
    echo "Installing kagglehub..."
    pip3 install kagglehub
    echo "[OK] kagglehub installed"
else
    echo "[OK] kagglehub already installed"
fi

echo
echo "========================================"
echo "  Starting Training..."
echo "========================================"
echo
echo "This will:"
echo "  1. Download Enron dataset (5,000 emails)"
echo "  2. Auto-label emails by category"
echo "  3. Train improved classifier"
echo "  4. Show accuracy results"
echo "  5. Save trained model"
echo
read -p "Press Enter to continue..."

# Run training
python3 train_with_enron.py

echo
echo "========================================"
echo "  Training Complete!"
echo "========================================"
echo
