#!/bin/bash

# Kill any existing WebSocket server processes
echo "Stopping any existing WebSocket servers on port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
pkill -f ultimate_do_button_server.py 2>/dev/null || true
pkill -f fixed_ultimate_do_button_server.py 2>/dev/null || true
pkill -f "python.*8765" 2>/dev/null || true
sleep 2

# Start the fixed WebSocket server
echo "Starting fixed Ultimate DO Button Server..."
cd "$(dirname "$0")"
python3 fixed_ultimate_do_button_server.py --debug > logs/websocket/ultimate_do_button_server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > pids/ultimate_do_button_server.pid
echo "Ultimate DO Button Server PID: $SERVER_PID"

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Ultimate DO Button Server started successfully!"
    echo "Run the suggestion test script with:"
    echo "python3 simplified_suggestion_fix.py \"Test Suggestion\" \"This is a test suggestion\""
else
    echo "❌ Failed to start Ultimate DO Button Server!"
    echo "Check logs for errors: logs/websocket/ultimate_do_button_server.log"
    exit 1
fi