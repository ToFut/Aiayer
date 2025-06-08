#!/bin/bash
# Script to start the fixed DO button test framework

echo "Starting fixed DO button test framework..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if the script files exist
if [ ! -f "fixed_agent_do_button_exam.py" ]; then
    echo "Error: fixed_agent_do_button_exam.py not found."
    exit 1
fi

if [ ! -f "fixed_agent_do_button_exam.html" ]; then
    echo "Error: fixed_agent_do_button_exam.html not found."
    exit 1
fi

# Create screenshots directory if it doesn't exist
mkdir -p test_screenshots

# Kill any existing processes on port 8767
echo "Checking for existing processes on port 8767..."
if lsof -i :8767 &> /dev/null; then
    echo "Killing existing process on port 8767..."
    lsof -ti :8767 | xargs kill -9
fi

# Start the WebSocket server with proper flags
echo "Starting fixed WebSocket server on port 8767..."
python3 fixed_agent_do_button_exam.py --port 8767 --host localhost --open-browser --generate-screenshots &

# Store the server process ID
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Write PID to a file for later cleanup
echo $SERVER_PID > .fixed_do_button_server.pid

echo "DO button test framework started successfully!"
echo "Access the interface at: file://$(pwd)/fixed_agent_do_button_exam.html"
echo "Press Ctrl+C to stop the server"

# Wait for Ctrl+C
trap "echo 'Stopping server...'; kill $SERVER_PID; rm .fixed_do_button_server.pid; echo 'Server stopped.'; exit 0" INT
wait $SERVER_PID