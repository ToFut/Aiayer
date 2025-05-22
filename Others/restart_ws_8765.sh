#!/bin/bash

# Restart script for WebSocket server on port 8765
# This script will stop any existing WebSocket server on port 8765 and start a new one

echo "Restarting WebSocket server on port 8765..."

# Kill any existing processes on port 8765
echo "Stopping existing WebSocket server..."
lsof -ti :8765 | xargs kill -9 2>/dev/null || true

# Wait a moment for the port to be released
sleep 2

# Start the WebSocket server
echo "Starting WebSocket server..."
python3 fixed_ws_8765.py &

# Wait for the server to start
sleep 2

# Check if the server is running
if lsof -ti :8765 >/dev/null; then
    echo "WebSocket server started successfully on port 8765"
else
    echo "Failed to start WebSocket server"
    exit 1
fi

echo "Done!"