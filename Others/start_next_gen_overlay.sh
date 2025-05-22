#!/bin/bash

# Next Generation Overlay Startup Script
# This script launches the advanced bridge server and sets up the overlay system

# Create logs directory if it doesn't exist
mkdir -p logs

# Create memory directory if it doesn't exist
mkdir -p memory

# Kill any existing processes
echo "Stopping any existing processes..."
pkill -f "advanced_bridge.py" || true
pkill -f "python -m http.server --directory . 8080" || true

# Log the start
echo "$(date) - Starting Next Gen Overlay System" >> logs/startup.log

# Start the bridge server in the background
echo "Starting Advanced Bridge Server..."
python3 advanced_bridge.py > logs/bridge_output.log 2>&1 &
BRIDGE_PID=$!

# Save PID
echo $BRIDGE_PID > pids/bridge_server.pid
echo "Bridge server started with PID $BRIDGE_PID"

# Wait a moment for the bridge to initialize
sleep 2

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
echo "=== Next Gen Overlay System Started ==="
echo "Advanced Bridge running on ports: 8765 (frontend), 8766 (backend)"
echo "Overlay UI available at: http://localhost:8080/futuristic_overlay.html"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running to make it easier to kill everything with Ctrl+C
trap "echo 'Stopping services...'; kill $BRIDGE_PID $HTTP_PID 2>/dev/null; exit" INT TERM
wait $BRIDGE_PID