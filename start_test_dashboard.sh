#!/bin/bash
# Start the SensAI/Aiayer Test Dashboard

# Ensure script is run from the project root
cd "$(dirname "$0")"

# Create necessary directories
mkdir -p logs
mkdir -p test_results
mkdir -p dashboard

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Kill any existing dashboard process
pkill -f "python3 test_dashboard.py" > /dev/null 2>&1

# Start the dashboard server
echo "Starting Test Dashboard..."
python3 test_dashboard.py

# If the server was killed with Ctrl+C, exit gracefully
echo "Test Dashboard stopped."