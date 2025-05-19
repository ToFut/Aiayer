#!/bin/bash
# start_working_system.sh
# A simplified script that ensures all components start properly

echo "=== Starting Aiayer System with WebSocket Only ==="

# Step 1: Kill any running processes
echo "Step 1: Stopping any running processes..."

# Kill any processes using port 8765
echo "Checking for processes using port 8765..."
port_pid=$(lsof -ti :8765 2>/dev/null)
if [ -n "$port_pid" ]; then
  echo "Killing process $port_pid using port 8765"
  kill -9 $port_pid 2>/dev/null || echo "Process $port_pid already gone"
  sleep 1
fi

# Kill specific processes
pkill -f "python.*sensor" 2>/dev/null || echo "No sensor processes found"
pkill -f "connect_sensor_to_memory" 2>/dev/null || echo "No connector processes found"
pkill -f "fixed_ws_8767" 2>/dev/null || echo "No WebSocket server found"
pkill -f "eye_server" 2>/dev/null || echo "No eye server found"

# Clean up PID files
echo "Cleaning up PID files..."
mkdir -p pids
rm -f pids/*.pid

# Create required directories
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory
mkdir -p logs/sensors
mkdir -p logs/memory

# Step 2: Start backend services
echo "Step 2: Starting backend services..."

# Start process sensor
echo "Starting process sensor..."
python3 sensors/process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
PROCESS_SENSOR_PID=$!
echo $PROCESS_SENSOR_PID > pids/process_sensor.pid
echo "Process sensor started with PID $PROCESS_SENSOR_PID"

# Start screen sensor
echo "Starting screen sensor..."
python3 sensors/screen_sensor.py > logs/sensors/screen_sensor.log 2>&1 &
SCREEN_SENSOR_PID=$!
echo $SCREEN_SENSOR_PID > pids/screen_sensor.pid
echo "Screen sensor started with PID $SCREEN_SENSOR_PID"

# Start file sensor
echo "Starting file sensor..."
python3 sensors/file_sensor.py > logs/sensors/file_sensor.log 2>&1 &
FILE_SENSOR_PID=$!
echo $FILE_SENSOR_PID > pids/file_sensor.pid
echo "File sensor started with PID $FILE_SENSOR_PID"

# Start memory connector
echo "Starting memory connector..."
python3 memory/connect_sensor_to_memory.py > logs/memory/connector.log 2>&1 &
CONNECTOR_PID=$!
echo $CONNECTOR_PID > pids/connector.pid
echo "Memory connector started with PID $CONNECTOR_PID"

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 3

# Step 3: Start the WebSocket server
echo "Step 3: Starting WebSocket server on port 8765..."

# Start the fixed WebSocket server
python3 fixed_ws_8765.py > logs/fixed_ws_8765.log 2>&1 &
WS_SERVER_PID=$!
echo $WS_SERVER_PID > pids/ws_server_8765.pid
echo "Fixed WebSocket server started with PID $WS_SERVER_PID"

# Wait for server to initialize
sleep 2

# Verify WebSocket server is running
if lsof -ti :8765 > /dev/null; then
    echo "✅ WebSocket server is running on port 8765"
else
    echo "❌ WebSocket server failed to start on port 8765"
    echo "Checking logs..."
    cat logs/fixed_ws_8765.log
    exit 1
fi

echo "=== System Started Successfully ==="
echo "Process sensor PID: $PROCESS_SENSOR_PID"
echo "Screen sensor PID: $SCREEN_SENSOR_PID"
echo "File sensor PID: $FILE_SENSOR_PID"
echo "Connector PID: $CONNECTOR_PID"
echo "WebSocket server PID: $WS_SERVER_PID"
echo ""
echo "IMPORTANT: The WebSocket server is running on port 8765"
echo "Connect Tauri app to: ws://127.0.0.1:8765"
echo ""
echo "To start Tauri overlay:"
echo "cd overlay && npm run tauri dev"
echo ""
echo "To check logs, use:"
echo "tail -f logs/fixed_ws_8765.log    # WebSocket server logs"
echo "tail -f logs/memory/connector.log # Memory connector logs"
echo "tail -f logs/sensors/process_sensor.log # Process sensor logs"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid)"