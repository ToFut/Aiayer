#!/bin/bash
# Script to run the enhanced WebSocket server with memory system integration

# Ensure the directory structure exists
mkdir -p logs pids

# Set up Python environment (if needed)
# source venv/bin/activate

# Kill any existing processes
echo "Checking for existing processes..."
if [ -f pids/ws_server_8765.pid ]; then
    PID=$(cat pids/ws_server_8765.pid)
    if ps -p $PID > /dev/null; then
        echo "Killing existing WebSocket server process: $PID"
        kill -9 $PID || true
    fi
    rm pids/ws_server_8765.pid
fi

# Start the enhanced WebSocket server
echo "Starting enhanced WebSocket server on port 8765..."
python3 enhanced_ws_8765.py &

# Wait for server to start
sleep 2

# Check if server started successfully
if [ -f pids/ws_server_8765.pid ]; then
    PID=$(cat pids/ws_server_8765.pid)
    if ps -p $PID > /dev/null; then
        echo "WebSocket server started successfully. PID: $PID"
    else
        echo "WebSocket server failed to start."
        exit 1
    fi
else
    echo "WebSocket server PID file not found."
    exit 1
fi

echo "WebSocket server is running. Press Ctrl+C to stop."
tail -f logs/enhanced_ws_8765.log