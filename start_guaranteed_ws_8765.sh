#!/bin/bash
#
# start_guaranteed_ws_8765.sh
#
# This script starts the WebSocket server on port 8765 specifically
# for handling notifications to the overlay UI.
#

echo "Starting WebSocket server on port 8765..."

# First, kill any existing processes on port 8765
if lsof -ti:8765 >/dev/null; then
  echo "Stopping existing WebSocket server on port 8765..."
  lsof -ti:8765 | xargs kill -9
  sleep 2
fi

# Create required directories
mkdir -p logs
mkdir -p pids

# Make the script executable
chmod +x fixed_ws_server_8765.py

# Start the server
python3 fixed_ws_server_8765.py > logs/ws_server_8765.log 2>&1 &

# Save PID
PID=$\!
echo $PID > pids/ws_server_8765.pid
echo "WebSocket server started with PID: $PID"

# Wait a moment and check if it is running
sleep 3
if ps -p $PID > /dev/null; then
  echo "✅ WebSocket server is running on port 8765"
  
  # Verify WebSocket is listening
  if lsof -i :8765 | grep LISTEN; then
    echo "✅ WebSocket server is listening on port 8765"
  else
    echo "❌ WebSocket server is not listening on port 8765"
    echo "Check logs/ws_server_8765.log for errors"
    tail -n 20 logs/ws_server_8765.log
  fi
else
  echo "❌ WebSocket server failed to start"
  echo "Check logs/ws_server_8765.log for errors"
  tail -n 20 logs/ws_server_8765.log
fi

echo "Done."
