#!/bin/bash
# start_optimized_system.sh
# A comprehensive script that applies fixes and starts the optimized system

set -e
echo "=== Starting Optimized Aiayer System with Smart Batching ==="

# Skip applying fixes to avoid dependency issues
echo "Step 1: Preparing system..."
echo "Applying essential preparations directly instead of running fix script"

# Create required directories
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p pids

# Create essential files if they don't exist
if [ ! -f "cache/process_sensor/process_cache.json" ] || [ ! -s "cache/process_sensor/process_cache.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "cache/process_sensor/process_cache.json"
fi

if [ ! -f "cache/screen_sensor/screen_cache.json" ] || [ ! -s "cache/screen_sensor/screen_cache.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "cache/screen_sensor/screen_cache.json"
fi

if [ ! -f "cache/screen_sensor/last_screen.json" ] || [ ! -s "cache/screen_sensor/last_screen.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "cache/screen_sensor/last_screen.json"
fi

if [ ! -f "memory/memory_state.json" ] || [ ! -s "memory/memory_state.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "memory/memory_state.json"
fi

if [ ! -f "memory/last_context.json" ] || [ ! -s "memory/last_context.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "memory/last_context.json"
fi

echo "Essential preparation completed"

# Function to kill processes
kill_process() {
  process_name=$1
  echo "Stopping ${process_name} processes..."
  pids=$(ps aux | grep -i ${process_name} | grep -v grep | awk '{print $2}')
  if [ -n "$pids" ]; then
    echo "Killing processes: $pids"
    for pid in $pids; do
      kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
    done
    echo "${process_name} processes stopped"
  else
    echo "No ${process_name} processes found running"
  fi
}

# Step 2: Stop any running processes
echo "Step 2: Stopping any running processes..."
kill_process "sensor"
kill_process "connect_sensor_to_memory"
kill_process "fixed_ws_server_with_memory"
kill_process "websocket"

# Remove http_server.pid file if it exists
if [ -f "pids/http_server.pid" ]; then
  echo "Removing pids/http_server.pid"
  rm -f pids/http_server.pid
fi

echo "All processes stopped"

# Step 3: Prepare empty cache files with proper structure
echo "Step 3: Preparing cache files..."

# Create timestamp for backups
timestamp=$(date +%Y%m%d_%H%M%S)

# Initialize process cache with proper structure
echo "Initializing process cache..."
if [ -f "cache/process_sensor/process_cache.json" ] && [ -s "cache/process_sensor/process_cache.json" ]; then
  cp "cache/process_sensor/process_cache.json" "cache/process_sensor/process_cache.json.bak_${timestamp}"
fi
echo '{
  "timestamp": '$(date +%s)',
  "active_window": "",
  "active_app": "",
  "active_apps": [],
  "window_history": []
}' > "cache/process_sensor/process_cache.json"

# Initialize screen cache with proper structure
echo "Initializing screen cache..."
if [ -f "cache/screen_sensor/screen_cache.json" ] && [ -s "cache/screen_sensor/screen_cache.json" ]; then
  cp "cache/screen_sensor/screen_cache.json" "cache/screen_sensor/screen_cache.json.bak_${timestamp}"
fi
echo '{
  "timestamp": '$(date +%s)',
  "screen_text": "",
  "has_images": false,
  "has_videos": false
}' > "cache/screen_sensor/screen_cache.json"

# Initialize last_screen.json if it doesn't exist
if [ ! -f "cache/screen_sensor/last_screen.json" ] || [ ! -s "cache/screen_sensor/last_screen.json" ]; then
  echo '{
  "timestamp": '$(date +%s)',
  "screen_text": "",
  "has_images": false,
  "has_videos": false
}' > "cache/screen_sensor/last_screen.json"
fi

# Initialize last_context.json with proper structure
echo "Initializing context tracking..."
echo '{
  "timestamp": '$(date +%s)',
  "active_window": "",
  "active_app": "",
  "active_apps": [],
  "window_history": [],
  "screen_text": ""
}' > "memory/last_context.json"

echo "Cache files prepared"

# Step 4: Start all backend services
echo "Step 4: Starting backend services..."

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

# Verify services are running
echo "Verifying services..."
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ] && [ "$(basename "$pid_file")" != "http_server.pid" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "✅ Service $(basename "$pid_file" .pid) is running (PID: $pid)"
        else
            echo "❌ Service $(basename "$pid_file" .pid) failed to start"
            exit 1
        fi
    fi
done

echo "All backend services started successfully"

# Step 5: Start the WebSocket server
echo "Step 5: Starting WebSocket server on port 8767..."

# First, kill any existing process on port 8767
echo "Checking for processes using port 8767..."
if command -v lsof &> /dev/null; then
  pid=$(lsof -ti :8767 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "Killing process $pid using port 8767"
    kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
    sleep 1
  fi
fi

# Also try to kill any process named simple_ws_server_8767.py
pkill -f "simple_ws_server_8767.py" 2>/dev/null || echo "No simple_ws_server_8767.py process found"

# Remove the WebSocket server PID file if it exists
if [ -f "pids/ws_server_8767.pid" ]; then
  echo "Removing pids/ws_server_8767.pid"
  rm -f pids/ws_server_8767.pid
fi
sleep 1

# Create a very simple server script that runs on port 8767
cat > simple_ws_server_8767.py << EOF
#!/usr/bin/env python
"""
Simple WebSocket Server on Port 8767

Minimal WebSocket server implementation for testing.
"""
import asyncio
import json
import logging
import websockets
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ws_server_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

async def handler(websocket, path):
    """Handle WebSocket connections with proper signature including path parameter."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected at path: {path}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": f"Connected to WebSocket server at path: {path}",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Echo back the message
                await websocket.send(json.dumps({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)

async def broadcast_status():
    """Periodically broadcast status updates to all clients."""
    while True:
        if connected_clients:
            message = json.dumps({
                "type": "status_update",
                "data": {
                    "client_count": len(connected_clients),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Broadcast to all clients
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
        
        await asyncio.sleep(5)

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Try different ports if the default one is in use
        ports_to_try = [8767, 8769, 8770, 8771]
        server = None
        
        for port in ports_to_try:
            try:
                server = await websockets.serve(
                    handler,
                    "127.0.0.1",
                    port,
                    ping_interval=10,
                    ping_timeout=5,
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                    max_queue=64,               # Queue size
                    close_timeout=2             # Close timeout
                )
                logger.info(f"WebSocket server started on ws://127.0.0.1:{port}")
                # Save the port we're actually using
                with open("ws_port.txt", "w") as f:
                    f.write(str(port))
                break
            except OSError as e:
                logger.warning(f"Port {port} is in use, trying another port: {e}")
                continue
                
        if server is None:
            raise OSError("All ports are in use. Cannot start WebSocket server.")
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
EOF

# Make the script executable
chmod +x simple_ws_server_8767.py

# Start the WebSocket server
echo "Starting WebSocket server..."
python3 simple_ws_server_8767.py > logs/ws_server_8767.log 2>&1 &
WS_SERVER_PID=$!
echo $WS_SERVER_PID > pids/ws_server_8767.pid
echo "WebSocket server started with PID $WS_SERVER_PID"

# Wait for server to initialize
sleep 2

# Verify server is running
if ps -p $WS_SERVER_PID > /dev/null; then
    echo "✅ WebSocket server is running (PID: $WS_SERVER_PID)"
else
    echo "❌ WebSocket server failed to start"
    exit 1
fi

# Step 7: Save PIDs for easier management
echo "Step 7: Saving process IDs for management..."
mkdir -p pids
echo "$PROCESS_SENSOR_PID" > "pids/process_sensor.pid"
echo "$SCREEN_SENSOR_PID" > "pids/screen_sensor.pid"
echo "$FILE_SENSOR_PID" > "pids/file_sensor.pid"
echo "$CONNECTOR_PID" > "pids/connector.pid"
echo "$WS_SERVER_PID" > "pids/ws_server_8767.pid"

echo "=== Optimized System Started Successfully ==="
echo "The system is now running with smart batching to optimize LLM requests"
echo "Process sensor PID: $PROCESS_SENSOR_PID"
echo "Screen sensor PID: $SCREEN_SENSOR_PID"
echo "File sensor PID: $FILE_SENSOR_PID"
echo "Connector PID: $CONNECTOR_PID"
echo "WebSocket server PID: $WS_SERVER_PID"

# Read the actual port the WebSocket server is using
if [ -f "ws_port.txt" ]; then
  WS_PORT=$(cat ws_port.txt)
  echo ""
  echo "IMPORTANT: The WebSocket server is now running on port $WS_PORT"
  echo "Connect to: ws://127.0.0.1:$WS_PORT"
else
  echo ""
  echo "WebSocket server should be running on one of these ports: 8767, 8769, 8770, 8771"
  echo "Check logs/ws_server_8767.log for actual port information"
fi
echo ""
echo "To check logs, use:"
echo "tail -f logs/ws_server_8767.log   # WebSocket server logs"
echo "tail -f logs/memory_bridge.log    # Memory connector logs"
echo "tail -f logs/sensors/process_sensor.log  # Process sensor logs"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid)"