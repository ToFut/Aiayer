#!/bin/bash

# Start the WebSocket server in the background
echo "Starting WebSocket server on port 8765..."
python3 ws_server_8765.py &
WS_PID=$!

# Give it a moment to start
sleep 2

# Start Tauri dev server
echo "Starting Tauri dev server..."
npm run tauri dev

# When Tauri exits, kill the WebSocket server
echo "Shutting down WebSocket server..."
kill $WS_PID