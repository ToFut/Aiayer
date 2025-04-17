#!/bin/bash

# Minimal run script for Local AI Assistant

# Create necessary directories
mkdir -p logs
mkdir -p config

# Set up Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Clean up previous packages to avoid conflicts
pip uninstall -y pyyaml pillow flask-sock mss pytesseract watchdog websockets

# Install minimal dependencies
echo "Installing minimal dependencies..."
pip install --upgrade pip
pip install Flask python-dotenv flask-cors pyyaml pillow flask-sock mss pytesseract watchdog websockets requests

# Set environment variables
export PYTHONPATH=.
export FLASK_DEBUG=1
export FLASK_APP=main.py

# Start the application
echo "Starting the application..."
python3 main.py