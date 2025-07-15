#!/bin/bash

# SensAI Fixed System Startup Script
# This script starts all components with the latest fixes applied

echo "🚀 Starting SensAI Fixed System..."

# Kill any existing processes
echo "🔄 Stopping existing processes..."
pkill -f "python.*backend" 2>/dev/null
pkill -f "python.*overlay" 2>/dev/null
pkill -f "python.*chat" 2>/dev/null
pkill -f "python.*bridge" 2>/dev/null
sleep 3

# Start backend server
echo "🔧 Starting backend server..."
python enhanced_enterprise_backend_with_context.py &
BACKEND_PID=$!
echo $BACKEND_PID > pids/aiayer_backend.pid
sleep 2

# Start chat server
echo "💬 Starting chat server..."
python ui/chat_server.py &
CHAT_PID=$!
echo $CHAT_PID > pids/chat_server.pid
sleep 2

# Start bridge server
echo "🌉 Starting bridge server..."
python bridge/server.py &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
sleep 2

# Start overlay
echo "🖥️ Starting overlay..."
cd overlay && npm run tauri dev &
OVERLAY_PID=$!
echo $OVERLAY_PID > ../pids/overlay.pid
cd ..

echo "✅ SensAI Fixed System started successfully!"
echo "📊 Process PIDs:"
echo "   Backend: $BACKEND_PID"
echo "   Chat: $CHAT_PID"
echo "   Bridge: $BRIDGE_PID"
echo "   Overlay: $OVERLAY_PID"
echo ""
echo "🌐 Access points:"
echo "   Overlay: http://localhost:1420"
echo "   Chat: http://localhost:5000"
echo "   Backend: http://localhost:8765"
echo ""
echo "🎯 Try typing: 'Write Segev in Google'"