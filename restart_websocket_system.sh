#!/bin/bash

echo "🔄 Restarting WebSocket Components with Enhanced Timeout Settings..."

# Stop existing WebSocket servers
echo "🛑 Stopping existing WebSocket servers..."
pkill -f "real_llm_backend_8767" 2>/dev/null || true
pkill -f "direct_coordinate_automation" 2>/dev/null || true
pkill -f "ws_server_8765" 2>/dev/null || true
pkill -f "fixed_bridge_server" 2>/dev/null || true
sleep 2

# Clean up any processes using the required ports
echo "🧹 Cleaning up port usage..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true
sleep 1

# Ensure log directories exist
echo "📁 Creating log directories..."
mkdir -p logs/backend
mkdir -p logs/websocket
mkdir -p pids

# Start the backend with enhanced timeout settings
echo "🚀 Starting Real LLM Backend with enhanced timeout settings..."
python3 real_llm_backend_8767.py > logs/backend/real_llm_8767.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/real_llm_backend_8767.pid
echo "Backend PID: $BACKEND_PID"
sleep 3

# Start the DO Button WebSocket server
echo "🚀 Starting DO Button WebSocket Server..."
python3 direct_coordinate_automation.py > logs/websocket/direct_coordinate_automation.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > pids/direct_coordinate_automation.pid
echo "DO Button PID: $DO_BUTTON_PID"
sleep 2

# Verify the servers are running
echo "🔍 Verifying WebSocket servers..."

if lsof -i :8767 > /dev/null 2>&1; then
    echo "✅ Backend WebSocket Server is running on port 8767"
else
    echo "❌ Backend WebSocket Server is NOT running on port 8767"
fi

if lsof -i :8765 > /dev/null 2>&1; then
    echo "✅ DO Button WebSocket Server is running on port 8765"
else
    echo "❌ DO Button WebSocket Server is NOT running on port 8765"
fi

echo ""
echo "✅ WebSocket systems restarted with enhanced timeout settings"
echo ""
echo "📋 Connection configuration in overlay:"
echo "  - DO Button: ws://localhost:8765"
echo "  - Backend:   ws://localhost:8767"
echo ""
echo "💡 To verify connections: python3 debug_overlay_websocket.py"
echo "📊 To monitor backend logs: tail -f logs/backend/real_llm_8767.log"