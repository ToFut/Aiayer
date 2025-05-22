#!/bin/bash

# Next Generation Overlay Startup Script (Without HTTP Server)
# This script launches only the advanced bridge server for the Tauri overlay

# Create logs directory if it doesn't exist
mkdir -p logs

# Create memory directory if it doesn't exist
mkdir -p memory

# Create pids directory if it doesn't exist
mkdir -p pids

# Kill any existing processes
echo "Stopping any existing processes..."
pkill -f "advanced_bridge.py" || true

# Log the start
echo "$(date) - Starting Next Gen Overlay System (WebSocket Only)" >> logs/startup.log

# Start the bridge server in the background
echo "Starting Advanced Bridge Server..."
python3 advanced_bridge.py > logs/bridge_output.log 2>&1 &
BRIDGE_PID=$!

# Save PID
echo $BRIDGE_PID > pids/bridge_server.pid
echo "Bridge server started with PID $BRIDGE_PID"

echo ""
echo "=== Next Gen Overlay System Started (WebSocket Only) ==="
echo "Advanced Bridge running on ports: 8765 (frontend), 8766 (backend)"
echo "Ready for Tauri application to connect"
echo ""
echo "To start the Tauri application, run:"
echo "cd overlay && npm run tauri dev"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running to make it easier to kill everything with Ctrl+C
trap "echo 'Stopping services...'; kill $BRIDGE_PID 2>/dev/null; exit" INT TERM
wait $BRIDGE_PID