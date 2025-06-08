#!/bin/bash

# Script to restart the overlay system with fixed websocket connections
echo "Restarting overlay system with fixed WebSocket connections..."

# Navigate to the overlay directory
cd "$(dirname "$0")"

# Step 1: Kill any existing processes
echo "Stopping existing processes..."
pkill -f ai-assistant-overlay 2>/dev/null || true
pkill -f vite 2>/dev/null || true
pkill -f tauri 2>/dev/null || true

# Kill websocket servers
echo "Stopping existing WebSocket servers..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true
lsof -ti:8768 | xargs kill -9 2>/dev/null || true

# Give processes time to shut down
sleep 3

# Step 2: Start the enhanced enterprise backend
echo "Starting enhanced enterprise backend (8767)..."
cd ..
python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_8767.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/enhanced_enterprise_backend.pid
echo "Backend PID: $BACKEND_PID"

# Give backend time to initialize
sleep 3

# Step 3: Start the websocket bridge server
echo "Starting fixed bridge server (8768)..."
cd overlay
python3 fixed_bridge_server.py > logs/fixed_bridge.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/fixed_bridge.pid
echo "Bridge PID: $BRIDGE_PID"

# Step 4: Start minimal websocket server
echo "Starting minimal websocket server (8765)..."
python3 minimal_ws_server.py > logs/minimal_ws.log 2>&1 &
WS_PID=$!
echo $WS_PID > pids/minimal_ws.pid
echo "Minimal WebSocket server PID: $WS_PID"

# Give servers time to initialize
sleep 3

# Step 5: Start the overlay
echo "Starting overlay application..."
npm run tauri dev &
OVERLAY_PID=$!
echo $OVERLAY_PID > pids/overlay.pid
echo "Overlay PID: $OVERLAY_PID"

echo ""
echo "Overlay system restarted with fixed WebSocket connections!"
echo "- Enhanced enterprise backend on port 8767"
echo "- Fixed bridge server on port 8768"
echo "- Minimal WebSocket server on port 8765"
echo ""
echo "To stop the system, run: ./STOP_OVERLAY.sh"