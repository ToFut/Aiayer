#!/bin/bash

# Start Simple Brain Router System
# Fixes common startup issues

echo "🧠 STARTING SIMPLE BRAIN ROUTER SYSTEM"
echo "====================================="
echo "✨ Streamlined approach with all 4 modes"
echo ""

# Clean up any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "enhanced_enterprise_backend.py" 2>/dev/null
pkill -f "simple_brain_router_server.py" 2>/dev/null
pkill -f "brain_router.py" 2>/dev/null
sleep 2

# Check if port 8765 is available
if lsof -i :8765 > /dev/null 2>&1; then
    echo "⚠️  Port 8765 is in use, attempting to free it..."
    lsof -ti :8765 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Create directories
mkdir -p logs pids

echo "🚀 Starting Simple Brain Router..."

# Start the server
python3 simple_brain_router_server.py > logs/simple_brain_router.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > pids/simple_brain_router.pid

echo "⏳ Waiting for server to start..."
sleep 3

# Test connectivity
echo "🔍 Testing system connectivity..."
python3 test_brain_router_client.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SIMPLE BRAIN ROUTER SYSTEM READY!"
    echo "=================================="
    echo "🌐 WebSocket: ws://localhost:8765"
    echo "🧠 Brain Router: ACTIVE (PID: $SERVER_PID)"
    echo ""
    echo "📋 Available Modes:"
    echo "   🎯 Agent  - UI automation & task execution"
    echo "   💭 Ask    - Memory queries & knowledge retrieval"
    echo "   💡 Suggest - Proactive suggestions & optimization"
    echo "   🤖 General - Basic LLM conversations"
    echo ""
    echo "📝 Usage Example:"
    echo '{"type": "chat_request", "mode": "Agent", "message": "Click on Documents"}'
    echo ""
    echo "🛑 To stop: ./stop_simple_brain_router.sh"
    echo "📊 Logs: logs/simple_brain_router.log"
    echo "🔧 Test: python3 test_brain_router_client.py"
else
    echo "❌ STARTUP FAILED - Check logs/simple_brain_router.log"
    exit 1
fi