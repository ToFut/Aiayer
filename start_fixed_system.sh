#!/bin/bash
# start_fixed_system.sh
# A fixed version of the start script that won't hang

set -e
echo "=== Starting Fixed Aiayer System ==="

# Create required directories
echo "Creating required directories..."
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p pids

# Create essential files if they don't exist
echo "Creating essential files..."
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

# Stop any running processes
echo "Stopping any running processes..."
kill_process "sensor"
kill_process "connect_sensor_to_memory"
kill_process "fixed_ws_server_with_memory"
kill_process "websocket"
kill_process "simple_ws_server_8767"
echo "All processes stopped"

# Prepare cache files
echo "Preparing cache files..."
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

# Create a very simple server script that runs on port 8767
echo "Creating WebSocket server script..."
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
        # Create the server
        server = await websockets.serve(
            handler,
            "127.0.0.1",
            8767,
            ping_interval=10,
            ping_timeout=5,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            max_queue=64,               # Queue size
            close_timeout=2             # Close timeout
        )
        
        logger.info("WebSocket server started on ws://127.0.0.1:8767")
        
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

# Run the WebSocket server
echo "Starting WebSocket server..."
python3 simple_ws_server_8767.py > logs/ws_server_8767.log 2>&1 &
WS_SERVER_PID=$!
echo "WebSocket server started with PID $WS_SERVER_PID"
echo $WS_SERVER_PID > pids/ws_server_8767.pid

# Wait briefly to ensure the server starts
sleep 2

# Check if server is running
if command -v lsof &> /dev/null; then
    if lsof -ti :8767 &>/dev/null; then
        echo "✅ WebSocket server successfully running on port 8767"
    else
        echo "❌ WebSocket server failed to start on port 8767"
        echo "See logs/ws_server_8767.log for details"
    fi
fi

echo "=== System Started with WebSocket Server Only ==="
echo "The WebSocket server is now running on port 8767"
echo "Connect to: ws://127.0.0.1:8767"
echo ""
echo "To check logs, use:"
echo "tail -f logs/ws_server_8767.log   # WebSocket server logs"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid 2>/dev/null)"