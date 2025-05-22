#!/bin/bash
# start_optimized_system_fixed.sh
# Enhanced script with more robust checks and fixes for common issues

set -e
echo "=== Starting Enhanced Optimized Aiayer System ==="

# Function to print colored output
print_colored() {
    COLOR=$1
    TEXT=$2
    
    case $COLOR in
        "red") echo -e "\033[0;31m$TEXT\033[0m" ;;
        "green") echo -e "\033[0;32m$TEXT\033[0m" ;;
        "yellow") echo -e "\033[0;33m$TEXT\033[0m" ;;
        "blue") echo -e "\033[0;34m$TEXT\033[0m" ;;
        *) echo "$TEXT" ;;
    esac
}

# Function to check if directory exists and create if it doesn't
ensure_dir() {
    if [ ! -d "$1" ]; then
        print_colored "yellow" "Creating directory: $1"
        mkdir -p "$1"
    fi
}

# Function to kill processes
kill_process() {
    process_name=$1
    print_colored "yellow" "Stopping ${process_name} processes..."
    pids=$(ps aux | grep -i ${process_name} | grep -v grep | awk '{print $2}')
    if [ -n "$pids" ]; then
        print_colored "yellow" "Killing processes: $pids"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
        done
        print_colored "green" "${process_name} processes stopped"
    else
        print_colored "blue" "No ${process_name} processes found running"
    fi
}

# Step 1: Create required directories
print_colored "blue" "Step 1: Creating required directories..."
ensure_dir "cache/process_sensor"
ensure_dir "cache/screen_sensor"
ensure_dir "cache/file_sensor"
ensure_dir "memory"
ensure_dir "logs/sensors/sensor_process"
ensure_dir "logs/sensors/screen_sensor"
ensure_dir "logs/sensors/file_sensor"
ensure_dir "logs/memory"
ensure_dir "pids"

# Step 2: Create essential files if they don't exist
print_colored "blue" "Step 2: Creating essential files..."
if [ ! -f "cache/process_sensor/process_cache.json" ] || [ ! -s "cache/process_sensor/process_cache.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "cache/process_sensor/process_cache.json"
  print_colored "green" "Created process_cache.json"
fi

if [ ! -f "cache/screen_sensor/screen_cache.json" ] || [ ! -s "cache/screen_sensor/screen_cache.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "cache/screen_sensor/screen_cache.json"
  print_colored "green" "Created screen_cache.json"
fi

if [ ! -f "cache/screen_sensor/last_screen.json" ] || [ ! -s "cache/screen_sensor/last_screen.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "cache/screen_sensor/last_screen.json"
  print_colored "green" "Created last_screen.json"
fi

if [ ! -f "cache/file_sensor/last_file.json" ] || [ ! -s "cache/file_sensor/last_file.json" ]; then
  echo "{\"timestamp\": $(date +%s), \"events\": []}" > "cache/file_sensor/last_file.json"
  print_colored "green" "Created last_file.json"
fi

if [ ! -f "memory/memory_state.json" ] || [ ! -s "memory/memory_state.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "memory/memory_state.json"
  print_colored "green" "Created memory_state.json"
fi

if [ ! -f "memory/last_context.json" ] || [ ! -s "memory/last_context.json" ]; then
  echo "{\"timestamp\": $(date +%s)}" > "memory/last_context.json"
  print_colored "green" "Created last_context.json"
fi

# Step 3: Stop any running processes
print_colored "blue" "Step 3: Stopping any running processes..."
kill_process "sensor"
kill_process "connect_sensor_to_memory"
kill_process "fixed_ws_server_with_memory"
kill_process "websocket"
kill_process "simple_ws_server"
kill_process "fixed_simple_ws_server"
kill_process "ws_server"

# Remove any old pid files
rm -f pids/*.pid 2>/dev/null || true
print_colored "green" "All processes stopped and pid files removed"

# Step 4: Prepare cache files with proper structure
print_colored "blue" "Step 4: Preparing cache files with proper structure..."

# Create timestamp for backups
timestamp=$(date +%Y%m%d_%H%M%S)

# Initialize process cache with proper structure
print_colored "yellow" "Initializing process cache..."
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
print_colored "yellow" "Initializing screen cache..."
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

# Initialize file sensor cache
print_colored "yellow" "Initializing file sensor cache..."
if [ -f "cache/file_sensor/last_file.json" ] && [ -s "cache/file_sensor/last_file.json" ]; then
  cp "cache/file_sensor/last_file.json" "cache/file_sensor/last_file.json.bak_${timestamp}"
fi
echo '{
  "timestamp": '$(date +%s)',
  "events": []
}' > "cache/file_sensor/last_file.json"

# Initialize last_context.json with proper structure
print_colored "yellow" "Initializing context tracking..."
echo '{
  "timestamp": '$(date +%s)',
  "active_window": "",
  "active_app": "",
  "active_apps": [],
  "window_history": [],
  "screen_text": ""
}' > "memory/last_context.json"

print_colored "green" "Cache files prepared successfully"

# Step 5: Start backend services
print_colored "blue" "Step 5: Starting backend services..."

# Function to start a service and verify it's running
start_service() {
    SERVICE_NAME=$1
    COMMAND=$2
    LOG_FILE=$3
    PID_FILE=$4
    
    print_colored "yellow" "Starting ${SERVICE_NAME}..."
    $COMMAND > $LOG_FILE 2>&1 &
    SERVICE_PID=$!
    sleep 1
    
    # Check if process is still running
    if ps -p $SERVICE_PID > /dev/null; then
        echo $SERVICE_PID > $PID_FILE
        print_colored "green" "✅ ${SERVICE_NAME} started with PID $SERVICE_PID"
        return 0
    else
        print_colored "red" "❌ ${SERVICE_NAME} failed to start"
        return 1
    fi
}

# Start process sensor
start_service "process sensor" "python3 sensors/fixed_process_sensor.py" "logs/sensors/sensor_process/process_sensor.log" "pids/process_sensor.pid"
PROCESS_SENSOR_SUCCESS=$?

# Start screen sensor
start_service "screen sensor" "python3 sensors/fixed_screen_sensor.py" "logs/sensors/screen_sensor/screen_sensor.log" "pids/screen_sensor.pid"
SCREEN_SENSOR_SUCCESS=$?

# Start file sensor with specified paths
# Use home directory and current working directory by default
HOME_DIR=$(cd ~ && pwd)
CURRENT_DIR=$(pwd)
MONITORED_PATHS="[\"$HOME_DIR/Desktop\", \"$CURRENT_DIR\"]"

# Start file sensor using our new implementation
start_service "file sensor" "python3 sensors/file_sensor.py" "logs/sensors/file_sensor.log" "pids/file_sensor.pid" 
FILE_SENSOR_SUCCESS=$?

# Start memory connector
start_service "memory connector" "python3 memory/connect_sensor_to_memory.py" "logs/memory/connector.log" "pids/connector.pid"
MEMORY_CONNECTOR_SUCCESS=$?

# Wait for services to initialize
print_colored "yellow" "Waiting for services to initialize..."
sleep 3

# Start WebSocket server on port 8767 with our fixed implementation
print_colored "blue" "Step 6: Starting WebSocket server on port 8767..."

# Check if the fixed script exists
if [ ! -f "fixed_simple_ws_server_8767.py" ]; then
  print_colored "yellow" "Creating WebSocket server script..."
  
  # Create a simple WebSocket server script
  cat > fixed_simple_ws_server_8767.py << EOF
#!/usr/bin/env python
"""
Fixed WebSocket Server on Port 8767

Fixed implementation with correct handler signature.
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

# Make sure the handler has the correct signature
async def handler(websocket):
    """Handle WebSocket connections."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to WebSocket server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Echo back the message with some additional info
                response = {
                    "type": "response",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                
                # If it's a user interaction, add a special response
                if data.get('type') == 'user_interaction':
                    payload = data.get('payload', {})
                    if payload.get('type') == 'query':
                        response = {
                            "type": "query_response",
                            "payload": {
                                "query": payload.get('query', ''),
                                "response": f"Processed your query: {payload.get('query', '')}",
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                
                # Send the response
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
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
        port = 8767
        host = "127.0.0.1"
        
        # Create server
        server = await websockets.serve(
            handler,
            host,
            port,
            ping_interval=10,
            ping_timeout=5,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            max_queue=64,               # Queue size
            close_timeout=2             # Close timeout
        )
        
        logger.info(f"server listening on {host}:{port}")
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        
        # Save the port we're using
        with open("ws_port.txt", "w") as f:
            f.write(str(port))
            
        # Save PID
        with open("pids/ws_server_8767.pid", "w") as f:
            f.write(str(os.getpid()))
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Create directories if needed
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pids", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
EOF

  # Make the script executable
  chmod +x fixed_simple_ws_server_8767.py
fi

# Kill any existing WebSocket server on port 8767
pkill -f "simple_ws_server_8767.py" 2>/dev/null || true
pkill -f "fixed_simple_ws_server_8767.py" 2>/dev/null || true
sleep 1

# Start the WebSocket server
start_service "WebSocket server" "python3 fixed_simple_ws_server_8767.py" "logs/ws_server_8767.log" "pids/ws_server_8767.pid"
WS_SERVER_SUCCESS=$?

# Check if all components are running
print_colored "blue" "Step 7: Verifying all components are running..."

FAILED_SERVICES=""

if [ $PROCESS_SENSOR_SUCCESS -ne 0 ]; then
    FAILED_SERVICES="$FAILED_SERVICES Process Sensor,"
fi

if [ $SCREEN_SENSOR_SUCCESS -ne 0 ]; then
    FAILED_SERVICES="$FAILED_SERVICES Screen Sensor,"
fi

if [ $FILE_SENSOR_SUCCESS -ne 0 ]; then
    FAILED_SERVICES="$FAILED_SERVICES File Sensor,"
fi

if [ $MEMORY_CONNECTOR_SUCCESS -ne 0 ]; then
    FAILED_SERVICES="$FAILED_SERVICES Memory Connector,"
fi

if [ $WS_SERVER_SUCCESS -ne 0 ]; then
    FAILED_SERVICES="$FAILED_SERVICES WebSocket Server,"
fi

if [ -n "$FAILED_SERVICES" ]; then
    # Remove trailing comma
    FAILED_SERVICES=${FAILED_SERVICES%,}
    print_colored "red" "ERROR: The following services failed to start: $FAILED_SERVICES"
    print_colored "yellow" "Check logs for more information."
    
    print_colored "yellow" "For process sensor: tail -f logs/sensors/sensor_process/process_sensor.log"
    print_colored "yellow" "For screen sensor: tail -f logs/sensors/screen_sensor/screen_sensor.log"
    print_colored "yellow" "For file sensor: tail -f logs/sensors/file_sensor.log"
    print_colored "yellow" "For memory connector: tail -f logs/memory/connector.log"
    print_colored "yellow" "For WebSocket server: tail -f logs/ws_server_8767.log"
    
    exit 1
fi

# Print summary
print_colored "green" "=== Optimized System Started Successfully ==="
print_colored "blue" "The system is now running with these components:"
echo "- Process sensor (PID: $(cat pids/process_sensor.pid))"
echo "- Screen sensor (PID: $(cat pids/screen_sensor.pid))"
echo "- File sensor (PID: $(cat pids/file_sensor.pid))"
echo "- Memory connector (PID: $(cat pids/connector.pid))"
echo "- WebSocket server (PID: $(cat pids/ws_server_8767.pid))"

# Read the actual port the WebSocket server is using
if [ -f "ws_port.txt" ]; then
  WS_PORT=$(cat ws_port.txt)
  print_colored "blue" "WebSocket server is running on: ws://127.0.0.1:$WS_PORT"
else
  print_colored "yellow" "WebSocket server should be running on port 8767"
fi

print_colored "blue" "WebSocket bridge is running on: ws://localhost:8765"

echo ""
print_colored "yellow" "To check logs, use:"
echo "tail -f logs/ws_server_8767.log          # WebSocket server logs"
echo "tail -f logs/memory/connector.log        # Memory connector logs"
echo "tail -f logs/sensors/sensor_process/process_sensor.log  # Process sensor logs"
echo "tail -f logs/sensors/screen_sensor/screen_sensor.log   # Screen sensor logs"
echo "tail -f logs/sensors/file_sensor.log     # File sensor logs"

echo ""
print_colored "yellow" "To test WebSocket connectivity:"
print_colored "blue" "python3 test_websocket.py"

echo ""
print_colored "yellow" "To stop all services:"
print_colored "red" "kill \$(cat pids/*.pid)"

echo ""
print_colored "green" "For Tauri development:"
print_colored "blue" "cd overlay && npm run tauri dev"