#!/bin/bash

# SensAI AI-Powered Enterprise System Startup Script
# Complete system with AI planning, screen intelligence, and user interaction

echo "🚀 Starting SensAI AI-Powered Enterprise System..."
echo "🧠 Features: AI Planning + Screen Intelligence + User Interaction + Memory Integration"
echo "" 
echo "📋 System Components:"
echo "   ✅ Agent Mode - AI-powered task planning with screen intelligence"
echo "   ✅ Ask Mode - Memory-enhanced knowledge queries"
echo "   ✅ Suggest Mode - Contextual AI suggestions"
echo "   ✅ General Mode - LLM-powered conversations"
echo "   ✅ Interactive Approval System - Rich user interaction"
echo "   ✅ Screen Intelligence - Real-time UI analysis"
echo "   ✅ Memory Integration - Semantic search and storage"
echo ""
echo "🔧 Starting AI-Powered Backend Server..."

# Navigate to project directory
cd "$(dirname "$0")"

# Kill any existing servers
echo "🛑 Stopping any existing servers..."
pkill -f enterprise_backend_server
pkill -f backend_server
sleep 2

# Install required dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import cv2, numpy, PIL" 2>/dev/null || {
    echo "⚠️ Missing dependencies. Installing..."
    pip3 install opencv-python numpy pillow websockets
}

# Start the AI-powered enterprise backend server
echo "🚀 Starting AI-Powered Enterprise Backend Server..."
cd Others
python3 enterprise_backend_server_ai_powered.py &
BACKEND_PID=$!
echo "📊 AI Backend Server PID: $BACKEND_PID"

# Wait for server to start
echo "⏳ Waiting for AI backend server to initialize..."
sleep 8

# Check if server is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ AI-Powered Backend Server started successfully!"
    echo "🌐 WebSocket Server: ws://localhost:8767"
    echo ""
    echo "🎯 SYSTEM READY!"
    echo ""
    echo "🧠 **AI-POWERED FEATURES ACTIVE:**"
    echo "   • Intelligent task planning and decomposition"
    echo "   • Real-time screen analysis and UI detection"
    echo "   • Interactive approval system with rich UX"
    echo "   • Memory-enhanced responses with semantic search"
    echo "   • LLM-powered reasoning and decision making"
    echo ""
    echo "📱 **HOW TO USE:**"
    echo "   1. Run the interactive client: python3 interactive_approval_client.py"
    echo "   2. Or connect your client to ws://localhost:8767"
    echo "   3. Send agent requests like: 'click on Documents Folder'"
    echo "   4. Review and approve/adjust AI-generated execution plans"
    echo "   5. Watch as the system executes precise UI automation"
    echo ""
    echo "🧪 **EXAMPLE AGENT REQUESTS:**"
    echo "   • 'click on Documents Folder'"
    echo "   • 'open Safari and navigate to google.com'"
    echo "   • 'create a new folder called Projects'"
    echo "   • 'find and click the Settings button'"
    echo ""
    echo "📊 Server Logs: Others/logs/backend/enterprise_backend_ai_powered.log"
    echo "🛑 Stop System: ./STOP_AI_SYSTEM.sh"
    echo ""
    echo "💡 Press Ctrl+C to stop the system or run interactive client in another terminal"
    
    # Keep script running and show live logs
    echo "📋 Live Server Status:"
    tail -f logs/backend/enterprise_backend_ai_powered.log 2>/dev/null || echo "ℹ️  AI Server running in background (PID: $BACKEND_PID)"
else
    echo "❌ Failed to start AI backend server!"
    echo "🔧 Check logs for errors:"
    cat logs/backend/enterprise_backend_ai_powered.log 2>/dev/null || echo "No logs found"
    exit 1
fi
