#!/bin/bash

# Store all PIDs in a file for later cleanup
RUNNING_PIDS_FILE=".running_pids"
touch $RUNNING_PIDS_FILE
echo "$(date): Starting system" > $RUNNING_PIDS_FILE

# Create function to kill processes by port or PID
kill_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        echo "Stopping process on port $port..."
        lsof -t -i :$port | xargs kill -9 > /dev/null 2>&1
    fi
}

kill_process() {
    local pid=$1
    if ps -p $pid > /dev/null 2>&1; then
        echo "Stopping process with PID $pid..."
        kill -9 $pid > /dev/null 2>&1
    fi
}

cleanup_all() {
    echo "Cleaning up all processes..."
    # Kill all processes listed in the running PIDs file
    if [ -f $RUNNING_PIDS_FILE ]; then
        while read line; do
            if [[ $line =~ [0-9]+ ]]; then
                kill_process $line
            fi
        done < $RUNNING_PIDS_FILE
    fi
    # Also kill processes by port for extra safety
    kill_port 8765  # WebSocket server
    kill_port 8766  # Bridge
    kill_port 5001  # Main application
    kill_port 5002  # Overlay application
    kill_port 11434 # Ollama
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Handle script termination
trap cleanup_all EXIT

# Clean up any existing processes first
cleanup_all

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Local Assistant system..."

# Start Ollama
if command_exists ollama; then
    echo "Starting Ollama..."
    ollama serve > logs/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "$OLLAMA_PID # Ollama" >> $RUNNING_PIDS_FILE
    echo "Ollama started on port 11434 (PID: $OLLAMA_PID)"
    sleep 3  # Give Ollama time to start
else
    echo "WARNING: Ollama is not installed, continuing without it"
fi

# Start WebSocket server
echo "Starting WebSocket server..."
python websocket_server.py --port 8765 > logs/websocket.log 2>&1 &
WS_PID=$!
echo "$WS_PID # WebSocket" >> $RUNNING_PIDS_FILE
echo "WebSocket server started on port 8765 (PID: $WS_PID)"
sleep 2  # Give WebSocket server more time to start

# Start bridge
echo "Starting bridge service..."
python fix_bridge.py --listen-port 8766 --backend-port 8765 > logs/bridge.log 2>&1 &
BRIDGE_PID=$!
echo "$BRIDGE_PID # Bridge" >> $RUNNING_PIDS_FILE
echo "Bridge service started on port 8766 (PID: $BRIDGE_PID)"
sleep 2  # Give bridge more time to start

# Initialize all sensors
echo "Initializing sensors..."
python -c "
from sensors.screen_sensor import ScreenSensor
from sensors.file_sensor import FileSensor
from sensors.process_sensor import ProcessSensor
import time

# Initialize sensors to ensure they work
print('Initializing screen sensor...')
screen = ScreenSensor()
screen.start()

print('Initializing file sensor...')
file = FileSensor()
file.start()

print('Initializing process sensor...')
process = ProcessSensor()
process.start()

# Let them collect initial data
time.sleep(2)
print('Sensors initialized successfully')
" > logs/sensors_init.log 2>&1

# Start main application with task agent
echo "Starting main application with overlay support..."
python main_with_overlay.py > logs/main_app.log 2>&1 &  
MAIN_PID=$!
echo "$MAIN_PID # Main App" >> $RUNNING_PIDS_FILE
echo "Main application started on port 5002 (PID: $MAIN_PID)"
sleep 3  # Give main app time to start

echo 
echo "Attempting to start overlay UI..."
cd overlay
npm run tauri dev > ../logs/overlay.log 2>&1 &
OVERLAY_PID=$!
cd ..
echo "$OVERLAY_PID # Overlay UI" >> $RUNNING_PIDS_FILE
echo "Overlay UI started (PID: $OVERLAY_PID)"

echo
echo "All components started successfully!"
echo "- WebSocket server: ws://localhost:8765"
echo "- Bridge service:   ws://localhost:8766"
echo "- Main application: http://localhost:5002"
echo "- Overlay UI is launching (this may take a minute)"
echo
echo "Check logs for any issues:"
echo "tail -f logs/main_app.log logs/overlay.log logs/websocket.log"
echo
echo "To stop all components, press Ctrl+C or run ./stop.sh"