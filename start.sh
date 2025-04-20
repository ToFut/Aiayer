#!/bin/bash

# Comprehensive starter script for the Local Assistant
# This script runs all components in the correct order and ensures proper communication

echo "========================================================"
echo "  Starting Local Assistant System"
echo "========================================================"

# Enable debug logging for better diagnostics
echo "Enabling debug logging..."
sed -i "" 's/level=WARNING/level=INFO/g' config/logging.conf 2>/dev/null || true
sed -i "" 's/WARNING/INFO/g' config/logging.conf 2>/dev/null || true

# Set up trap to clean up processes on exit
trap 'cleanup' INT TERM EXIT
function cleanup {
    echo "Cleaning up processes..."
    if [ -f "$RUNNING_PIDS_FILE" ]; then
        while read line; do
            if [[ "$line" == *"#"* ]]; then
                pid=$(echo $line | cut -d '#' -f1 | xargs)
                name=$(echo $line | cut -d '#' -f2 | xargs)
                if ps -p $pid > /dev/null; then
                    echo "Stopping $name (PID: $pid)"
                    kill -15 $pid 2>/dev/null || kill -9 $pid 2>/dev/null
                fi
            fi
        done < "$RUNNING_PIDS_FILE"
    fi
    echo "Cleanup complete"
}

# Kill any existing processes first
for port in 8765 8766 5001 5002 11434; do
    if lsof -i :$port > /dev/null 2>&1; then
        PID=$(lsof -t -i :$port)
        echo "Killing process on port $port (PID: $PID)..."
        kill -9 $PID 2>/dev/null
    fi
done

# Create logs directory with proper permissions
mkdir -p logs
chmod 755 logs

# Store all PIDs in a file for later cleanup
RUNNING_PIDS_FILE=".running_pids"
touch $RUNNING_PIDS_FILE
echo "$(date): Starting system" > $RUNNING_PIDS_FILE

# Function to wait for a service to be available on a port
wait_for_service() {
    local port=$1
    local max_attempts=$2
    local attempt=0
    
    echo "Waiting for service on port $port..."
    while ! nc -z localhost $port >/dev/null 2>&1; do
        attempt=$((attempt+1))
        if [ $attempt -gt $max_attempts ]; then
            echo "Service on port $port not available after $max_attempts attempts"
            return 1
        fi
        echo "Waiting for service on port $port (attempt $attempt/$max_attempts)..."
        sleep 1
    done
    echo "Service on port $port is available!"
    return 0
}

# Start WebSocket server first
echo "Starting WebSocket server on port 8765..."
python websocket_server.py --port 8765 > logs/websocket.log 2>&1 &
WS_PID=$!
echo "$WS_PID # WebSocket Server" >> $RUNNING_PIDS_FILE

# Wait for WebSocket server to be available
wait_for_service 8765 10
if [ $? -ne 0 ]; then
    echo "Failed to start WebSocket server. Check logs/websocket.log for details."
    exit 1
fi
echo "WebSocket server started successfully (PID: $WS_PID)"

# Start LLM
if command -v ollama >/dev/null 2>&1; then
    echo "Starting Ollama LLM service..."
    ollama serve > logs/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "$OLLAMA_PID # Ollama LLM" >> $RUNNING_PIDS_FILE
    
    # Give Ollama time to start
    sleep 3
    echo "Ollama started (PID: $OLLAMA_PID)"
else
    echo "Ollama not found. The system will use alternative LLM if configured."
fi

# Start main application with overlay support
echo "Starting main application..."
python main_with_overlay.py > logs/main_app.log 2>&1 &
MAIN_PID=$!
echo "$MAIN_PID # Main Application" >> $RUNNING_PIDS_FILE

# Wait for main app to be available
wait_for_service 5002 15
if [ $? -ne 0 ]; then
    echo "Failed to start main application. Check logs/main_app.log for details."
    exit 1
fi
echo "Main application started successfully (PID: $MAIN_PID)"

# Start overlay UI
echo "Starting overlay UI..."
cd overlay

# Check if node_modules exists, if not, run npm install
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies for overlay..."
    npm install
fi

# Run with improved error handling
npm run tauri dev > ../logs/overlay.log 2>&1 &
OVERLAY_PID=$!
cd ..
echo "$OVERLAY_PID # Overlay UI" >> $RUNNING_PIDS_FILE
echo "Overlay UI starting (PID: $OVERLAY_PID)"

# Give the overlay a few seconds to start up
echo "Waiting for overlay UI to initialize..."
sleep 5

echo
echo "========================================================"
echo "  All components started!"
echo "========================================================"
echo
echo "Running services:"
echo "- WebSocket server: ws://localhost:8765 (PID: $WS_PID)"
echo "- Main application: http://localhost:5002 (PID: $MAIN_PID)"
echo "- Overlay UI (PID: $OVERLAY_PID)"
if [ -n "$OLLAMA_PID" ]; then
    echo "- Ollama LLM: http://localhost:11434 (PID: $OLLAMA_PID)"
fi
echo
echo "View logs:"
echo "- WebSocket: tail -f logs/websocket.log"
echo "- Main app: tail -f logs/main_app.log"
echo "- Overlay: tail -f logs/overlay.log"
echo
echo "To stop all services, run: ./stop.sh"
echo

echo
echo "==================================================="
echo "  Local Assistant System is running"
echo "==================================================="
echo
echo "System status:"
echo "- WebSocket server: ws://localhost:8765"
echo "- Main application: http://localhost:5002"
echo "- Overlay UI: The overlay should open automatically"
echo
echo "Troubleshooting tips:"
echo "- If the overlay doesn't appear, check logs/overlay.log"
echo "- If responses aren't showing, check logs/websocket.log and logs/main_app.log"
echo "- If a component crashes, run ./stop.sh and then ./start.sh again"
echo 
echo "To monitor logs in real-time use:"
echo "  tail -f logs/main_app.log"
echo "  tail -f logs/websocket.log"
echo "  tail -f logs/overlay.log"
echo
echo "To stop all components, press Ctrl+C in this terminal"
echo "or run './stop.sh' from another terminal."
echo

# Keep the script running so trap works properly when user cancels
echo "Press Ctrl+C to stop all components..."
while true; do
    sleep 10
done