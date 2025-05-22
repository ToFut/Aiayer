#!/bin/bash

# Enhanced Overlay System Startup Script
# This script launches the enhanced backend server and sets up the overlay system

# Ensure directories exist
mkdir -p logs
mkdir -p pids
mkdir -p memory

# Kill any existing processes
echo "Stopping any existing processes..."
pkill -f "enhanced_backend_server.py" || true
pkill -f "python -m http.server --directory . 8080" || true

# Log the start
echo "$(date) - Starting Enhanced Overlay System" >> logs/startup.log

# Start the enhanced backend server if not already running
if ! pgrep -f "enhanced_backend_server.py" > /dev/null; then
    echo "Starting Enhanced Backend Server..."
    python3 enhanced_backend_server.py > logs/enhanced_backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Save PID
    echo $BACKEND_PID > pids/enhanced_backend.pid
    echo "Enhanced backend server started with PID $BACKEND_PID"
    
    # Wait a moment for the backend to initialize
    sleep 2
else
    echo "Enhanced backend server is already running"
fi

# Start a simple HTTP server to serve the overlay HTML
echo "Starting HTTP server for overlay UI..."
python3 -m http.server --directory . 8080 > logs/http_server.log 2>&1 &
HTTP_PID=$!

# Save PID
echo $HTTP_PID > pids/http_server.pid
echo "HTTP server started with PID $HTTP_PID"

# Open the overlay in the default browser
echo "Opening overlay in browser..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "http://localhost:8080/futuristic_overlay.html"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "http://localhost:8080/futuristic_overlay.html"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    start "http://localhost:8080/futuristic_overlay.html"
else
    echo "Please open http://localhost:8080/futuristic_overlay.html in your browser"
fi

echo ""
echo "=== Enhanced Overlay System Started ==="
echo "Enhanced Backend Server running on port: 8765"
echo "Overlay UI available at: http://localhost:8080/futuristic_overlay.html"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running to make it easier to kill everything with Ctrl+C
trap "echo 'Stopping services...'; pkill -f enhanced_backend_server.py; kill $HTTP_PID 2>/dev/null; exit" INT TERM
wait