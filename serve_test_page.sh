#!/bin/bash
# Simple script to serve the test DO button HTML page

echo "🌐 Starting simple HTTP server on port 8080..."
echo "📋 Open http://localhost:8080/test_do_button.html in your browser"
echo "📝 Make sure the guaranteed WebSocket server is running on port 8765"
echo "   (Use ./START_ENHANCED_SYSTEM.sh or python3 guaranteed_ws_server_8765.py)"
echo ""
echo "Press Ctrl+C to stop"

# Start a simple HTTP server
python3 -m http.server 8080