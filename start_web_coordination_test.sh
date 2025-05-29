#!/bin/bash

echo "🤖 Starting AgentMode Coordination Test Dashboard"
echo "=================================================="

# Check if required packages are installed
echo "📦 Checking dependencies..."

if ! python3 -c "import websockets" 2>/dev/null; then
    echo "⚠️  websockets package not found. Installing..."
    pip3 install websockets
fi

# Start the web server
echo "🚀 Starting web coordination test server..."
echo ""
echo "📱 Once started, open your browser to:"
echo "   http://localhost:8080/web_coordination_test.html"
echo ""
echo "🎯 Features available:"
echo "   ✅ Real-time automation plan creation"
echo "   ✅ DO/DISMISS/ADJUST button testing"
echo "   ✅ UI element click coordinate detection"
echo "   ✅ Visual execution progress tracking"
echo "   ✅ TeamViewer integration simulation"
echo "   ✅ Performance metrics monitoring"
echo ""
echo "🔌 WebSocket connection on ws://localhost:8765"
echo "🌐 HTTP server on http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="

# Start the Python server
python3 web_test_server.py