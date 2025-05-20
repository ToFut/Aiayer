#!/bin/bash

echo "====================================================="
echo "    Starting Aiayer System with Tauri Overlay        "
echo "====================================================="

# 1. First check if WebSocket port is available
if command -v nc &>/dev/null && nc -z localhost 8765 2>/dev/null; then
    echo "⚠️  Port 8765 is already in use. Stopping existing services..."
    if [ -f "pids/ws_server_8765.pid" ]; then
        kill $(cat pids/ws_server_8765.pid) 2>/dev/null || true
        sleep 1
    fi
    pkill -f "python.*enhanced_server.py" 2>/dev/null || true
    sleep 1
fi

# 2. Create required directories
mkdir -p logs
mkdir -p pids
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory
mkdir -p memory/logs

# 3. Initialize essential cache files
echo "{}" > memory/memory_state.json
echo "{}" > memory/last_context.json
echo "[]" > cache/process_sensor/process_cache.json
echo "[]" > cache/file_sensor/last_file.json
echo "{}" > cache/screen_sensor/screen_cache.json

# 4. Create minimal but functional WebSocket server on port 8765
echo "Creating minimal WebSocket server on port 8765..."
cat > ./minimal_ws_8765.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/minimal_ws_8765.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_ws_8765')

# Track connected clients
connected_clients = set()

# Handle WebSocket connections (with both websocket and path parameters)
async def handler(websocket, path):
    """Handler with proper signature including path parameter"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Hello client {client_id}! You are connected on path: {path}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send fake system context periodically
        context_task = asyncio.create_task(send_context_updates(websocket, client_id))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                
                # Handle specific message types
                if data.get('type') == 'connection_established':
                    logger.info(f"Overlay client initialized: {data.get('payload', {})}")
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "capabilities": ["context_tracking", "suggestions", "screen_capture"]
                        }
                    }))
                else:
                    # Default echo response
                    response = {
                        "type": "response",
                        "payload": {
                            "message": f"Received {data.get('type', 'unknown')} message",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
        # Cancel context task when the loop breaks
        context_task.cancel()
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except asyncio.CancelledError:
        logger.info(f"Tasks for {client_id} cancelled")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_context_updates(websocket, client_id):
    """Send periodic context updates to simulate sensor data"""
    try:
        while True:
            # Create fake system context data
            context_data = {
                "type": "sensor_data",
                "payload": {
                    "timestamp": datetime.now().isoformat(),
                    "active_app": "Visual Studio Code",
                    "window_title": "project.py - Aiayer - VS Code",
                    "cpu_usage": 23.5,
                    "memory_usage": 42.8,
                    "processes": [
                        {"name": "Code", "id": 12345, "cpu": 12.3, "memory": 234.5},
                        {"name": "Chrome", "id": 12346, "cpu": 8.7, "memory": 412.8},
                        {"name": "Terminal", "id": 12347, "cpu": 1.2, "memory": 78.3}
                    ]
                }
            }
            
            try:
                await websocket.send(json.dumps(context_data))
                logger.debug(f"Sent context update to {client_id}")
            except Exception as e:
                logger.error(f"Error sending context to {client_id}: {e}")
                raise
                
            # Send every 10 seconds
            await asyncio.sleep(10)
            
    except asyncio.CancelledError:
        logger.debug(f"Context updates for {client_id} stopped")
        raise

async def main():
    # Bind to localhost on port 8765
    port = 8765
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket server on {host}:{port}")
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    with open('pids/ws_server_8765.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"WebSocket server started on ws://{host}:{port}")
    
    # Keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
EOF

# 5. Make script executable
chmod +x ./minimal_ws_8765.py

# 6. Launch the WebSocket server
echo "Starting WebSocket server on port 8765..."
python3 ./minimal_ws_8765.py &
WS_PID=$!
echo $WS_PID > pids/ws_server_8765.pid
sleep 2

# 7. Check if WebSocket server is running
if ps -p $WS_PID > /dev/null; then
    echo "✅ WebSocket server started successfully on port 8765"
else
    echo "❌ WebSocket server failed to start!"
    exit 1
fi

# 8. Check if we need to navigate to the overlay directory
echo "Looking for overlay directory..."
CURRENT_DIR=$(pwd)
if [ -d "$CURRENT_DIR/overlay" ]; then
    echo "Found overlay directory, entering..."
    cd "$CURRENT_DIR/overlay"
    echo "Now in $(pwd)"
elif [ -d "$CURRENT_DIR/overlay 2" ]; then 
    echo "Found 'overlay 2' directory, entering..."
    cd "$CURRENT_DIR/overlay 2"
    echo "Now in $(pwd)"
else
    echo "⚠️ Could not find overlay directory."
    if [ -d "$CURRENT_DIR/src-tauri" ]; then
        echo "Found src-tauri in current directory, assuming we're already in the overlay directory."
    else
        echo "❌ Cannot find overlay directory or src-tauri! Please run this script from the root project directory."
        kill $WS_PID
        exit 1
    fi
fi

# 9. Now start the Tauri app
if [ -f "package.json" ]; then
    echo "Starting Tauri overlay application..."
    
    # Make sure node_modules exists, if not run npm install
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies first..."
        npm install
    fi
    
    # Ensure pids directory exists in root or parent
    if [ -d "../pids" ]; then
        PIDS_DIR="../pids"
    else
        mkdir -p "../pids"
        PIDS_DIR="../pids"
    fi
    
    # Create a small wrapper script to track the tauri process
    WRAPPER_SCRIPT="/tmp/run_tauri_$$.sh"
    cat > $WRAPPER_SCRIPT << 'EOF'
#!/bin/bash
# Run Tauri with transparent window and save PID
TAURI_LOG=info npm run tauri dev -- --no-watch &
TAURI_PID=$!
echo $TAURI_PID > $1/tauri.pid
wait $TAURI_PID
EOF
    chmod +x $WRAPPER_SCRIPT
    
    # Run the wrapper script
    echo "Executing: npm run tauri dev"
    $WRAPPER_SCRIPT $PIDS_DIR &
    WRAPPER_PID=$!
    echo $WRAPPER_PID > $PIDS_DIR/tauri_wrapper.pid
    echo "✅ Tauri development process started"
else
    echo "❌ Package.json not found! Cannot start Tauri app."
    kill $WS_PID
    exit 1
fi

echo "
=====================================================
    Aiayer System Running with Tauri Overlay
=====================================================

1. WebSocket server running on ws://localhost:8765
2. Tauri overlay app should be launching

To monitor logs:
- WebSocket server: tail -f logs/minimal_ws_8765.log

To stop the system:
- Press Ctrl+C to stop this script
- Or run: kill $(cat pids/ws_server_8765.pid) $(cat pids/tauri.pid)
"

# Wait for the wrapper script to complete (which waits for Tauri)
wait $WRAPPER_PID || true

# When the Tauri process ends, clean up
echo "Cleaning up processes..."
kill $WS_PID 2>/dev/null || true

# Clean up any remaining Tauri processes
if [ -f "$PIDS_DIR/tauri.pid" ]; then
    TAURI_PID=$(cat "$PIDS_DIR/tauri.pid")
    kill $TAURI_PID 2>/dev/null || true
fi

echo "All processes stopped. System shutdown complete."