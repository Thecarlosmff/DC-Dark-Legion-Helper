#!/bin/bash

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 not found. Please install Python 3.10+ and re-run this script."
    exit
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo "To activate later, run: source venv/bin/activate"
echo "To run the app: python main.py"
