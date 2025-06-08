#!/bin/bash

echo "🔄 Restarting Complete System with Fixed Port Configuration..."
echo ""
echo "Port Architecture:"
echo "  🔌 8765: DO Button WebSocket Server (automation execution)"
echo "  🔌 8767: Enhanced Enterprise Backend (AI/LLM services)"
echo ""

# Stop existing system
echo "🛑 Stopping existing system..."
./STOP_FIXED_SYSTEM.sh
./STOP_ENHANCED_SYSTEM.sh
pkill -f "ws_server" 2>/dev/null || true
pkill -f "real_llm_backend_8767" 2>/dev/null || true
pkill -f "fixed_bridge_server" 2>/dev/null || true
pkill -f "direct_coordinate_automation" 2>/dev/null || true
sleep 2

# Clean up any processes using the required ports
echo "🧹 Cleaning up port usage..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true
sleep 1

# Start the fixed system components
echo "🚀 Starting backend system..."
./RESTART_FIXED_SYSTEM.sh
sleep 5

# Ensure the direct coordinate automation server is running on 8765
echo "🔍 Checking DO Button server (port 8765)..."
if ! lsof -i :8765 > /dev/null 2>&1; then
  echo "  ⚠️ DO Button server not running on port 8765"
  echo "  🚀 Starting DO Button server..."
  python3 direct_coordinate_automation.py > logs/websocket/direct_coordinate_automation.log 2>&1 &
  echo $! > pids/direct_coordinate_automation.pid
  sleep 2
else
  echo "  ✅ DO Button server already running on port 8765"
fi

# Verify the backend server is running on 8767
echo "🔍 Checking Enhanced Backend server (port 8767)..."
if ! lsof -i :8767 > /dev/null 2>&1; then
  echo "  ⚠️ Enhanced Backend not running on port 8767"
  echo "  🚀 Starting Enhanced Backend..."
  python3 real_llm_backend_8767.py > logs/backend/real_llm_8767.log 2>&1 &
  echo $! > pids/real_llm_backend_8767.pid
  sleep 3
else
  echo "  ✅ Enhanced Backend already running on port 8767"
fi

# Restart the overlay with fixed configuration
echo "💻 Restarting overlay with fixed configuration..."
./RESTART_OVERLAY.sh

echo ""
echo "✅ Complete system restart completed"
echo "⏱️ Please wait a few seconds for all components to initialize"
echo "🔍 Overlay is now configured to connect to:"
echo "  - DO Button: ws://localhost:8765 (automation & notifications)"
echo "  - LLM/Backend: ws://localhost:8767 (chat & responses)"
echo ""
echo "🗣️ Try sending a message in the overlay chat"
echo "📋 To verify connections: python3 debug_overlay_websocket.py"