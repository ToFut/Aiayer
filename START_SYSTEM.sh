#!/bin/bash

# SensAI Enterprise System Startup Script
# Complete Enterprise-Grade System with Working UI Automation

echo "🚀 Starting SensAI Enterprise System..."
echo "🎯 Features: 4 Chat Modes + Real UI Automation + LLM Integration"
echo "" 
echo "📋 System Components:"
echo "   ✅ Agent Mode - Real UI automation (mouse/keyboard control)"
echo "   ✅ Ask Mode - Knowledge queries with semantic search"
echo "   ✅ Suggest Mode - Contextual suggestions"
echo "   ✅ General Mode - General LLM conversations"
echo ""
echo "🔧 Starting Backend Server..."

# Navigate to project directory
cd "$(dirname "$0")"

# Kill any existing servers
echo "🛑 Stopping any existing servers..."
pkill -f enterprise_backend_server_fixed
pkill -f enterprise_backend_server
sleep 2

# Start the fixed enterprise backend server
echo "🚀 Starting Enterprise Backend Server with UI Automation..."
cd Others
python3 enterprise_backend_server_fixed.py &
BACKEND_PID=$!
echo "📊 Backend Server PID: $BACKEND_PID"

# Wait for server to start
echo "⏳ Waiting for backend server to initialize..."
sleep 5

# Check if server is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend Server started successfully!"
    echo "🌐 WebSocket Server: ws://localhost:8767"
    echo ""
    echo "🎯 SYSTEM READY!"
    echo ""
    echo "📱 How to Use:"
    echo "   1. Connect your client to ws://localhost:8767"
    echo "   2. Send chat_request messages with mode: 'agent'|'ask'|'suggest'|'general'"
    echo "   3. Agent mode will execute real UI automation commands"
    echo ""
    echo "🧪 Test Agent Mode:"
    echo "   Query: 'click at position 150 150'"
    echo "   Query: 'type hello world'"
    echo "   Query: 'press return key'"
    echo ""
    echo "📊 Server Logs: Others/server_debug.log"
    echo "🛑 Stop System: ./STOP_SYSTEM.sh"
    echo ""
    echo "💡 Press Ctrl+C to stop the system"
    
    # Keep script running and show live logs
    echo "📋 Live Server Status:"
    tail -f Others/server_debug.log 2>/dev/null || echo "ℹ️  Server running in background (PID: $BACKEND_PID)"
else
    echo "❌ Failed to start backend server!"
    echo "🔧 Check logs for errors:"
    cat Others/server_debug.log 2>/dev/null || echo "No logs found"
    exit 1
fi