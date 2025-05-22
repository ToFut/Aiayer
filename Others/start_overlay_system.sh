#!/bin/bash

# Start Overlay System Script
# This script starts the enhanced overlay bridge server and the Tauri overlay

echo "==== Starting Enhanced Overlay System ===="

# Create required directories
mkdir -p logs memory pids

# Kill any existing processes
echo "Stopping any existing processes..."
pkill -f "overlay_bridge_server.py" || true

# Set environment variables
export TAURI_OVERLAY_DEBUG=true

# Start the bridge server in the background
echo "Starting Enhanced Overlay Bridge Server..."
python3 overlay_bridge_server.py > logs/overlay_bridge.log 2>&1 &
BRIDGE_PID=$!

# Save PID
echo $BRIDGE_PID > pids/overlay_bridge.pid
echo "Bridge server started with PID $BRIDGE_PID"

# Wait a moment for the bridge to initialize
sleep 2

# Start the Tauri overlay application
echo "Starting Tauri Overlay Application..."
cd overlay

# Determine how to run the Tauri app based on environment
if [ -f "target/release/ai-assistant-overlay" ]; then
    # Production build exists, run that
    echo "Using production build..."
    ./target/release/ai-assistant-overlay &
    OVERLAY_PID=$!
else
    # Development mode with npm
    echo "Using development build..."
    npm run tauri dev &
    OVERLAY_PID=$!
fi

# Save PID
echo $OVERLAY_PID > ../pids/overlay_app.pid
echo "Overlay application started with PID $OVERLAY_PID"

echo ""
echo "=== Enhanced Overlay System Started ==="
echo "Bridge server running on ports: 8765 (frontend), 8766 (backend)"
echo "Overlay application running"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for bridge process to finish
wait $BRIDGE_PID

# On exit, clean up
echo "Stopping services..."
if [ -f "pids/overlay_app.pid" ]; then
    kill $(cat pids/overlay_app.pid) 2>/dev/null || true
fi

if [ -f "pids/overlay_bridge.pid" ]; then
    kill $(cat pids/overlay_bridge.pid) 2>/dev/null || true
fi

echo "Enhanced Overlay System stopped"