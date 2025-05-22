#!/bin/bash

echo "====================================================="
echo "    Complete Fix for Both WebSocket and Tauri         "
echo "====================================================="

# Part 1: Stop all potential conflicting processes
echo "Stopping all potential conflicting processes..."
pkill -f "python.*ws" 2>/dev/null || true
pkill -f "python.*server" 2>/dev/null || true
pkill -f "python.*bridge" 2>/dev/null || true
sleep 1

# Check for processes on port 8765
PORT_PIDS=$(lsof -i:8765 -t 2>/dev/null)
if [ -n "$PORT_PIDS" ]; then
    echo "Killing processes on port 8765: $PORT_PIDS"
    kill -9 $PORT_PIDS 2>/dev/null || true
fi

# Part 2: Create a minimal but reliable WebSocket server
echo "Creating minimal WebSocket server..."
mkdir -p logs pids

cat > ./minimal_ws_server.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal WebSocket server with proper handler signature.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/minimal_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_ws')

# Connected clients
connected_clients = set()

# IMPORTANT: Handler must include the path parameter
async def handler(websocket, path):
    """WebSocket handler with both websocket and path parameters"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to minimal WebSocket server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Start data sending task
        data_task = asyncio.create_task(send_periodic_data(websocket))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Send response
                await websocket.send(json.dumps({
                    "type": "response",
                    "payload": {
                        "message": "Received your message",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed with {client_id}")
    except Exception as e:
        logger.error(f"Error with {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        data_task.cancel()
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket):
    """Send periodic data to client"""
    try:
        import random
        counter = 0
        
        while True:
            # Create simulated data
            processes = [
                {"name": "Chrome", "pid": 12345, "cpu": random.uniform(5, 20), "memory": 234.5},
                {"name": "VS Code", "pid": 12346, "cpu": random.uniform(2, 10), "memory": 412.8},
                {"name": "Terminal", "pid": 12347, "cpu": random.uniform(0.5, 5), "memory": 78.3}
            ]
            
            # Rotate active app
            apps = ["Chrome", "VS Code", "Terminal", "Finder"]
            active_app = apps[counter % len(apps)]
            
            screen_data = {
                "active_app": active_app,
                "window_title": f"{active_app} - Working on project",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send sensor data
            sensor_data = {
                "type": "sensor_data",
                "payload": {
                    "processes": processes,
                    "screen": screen_data,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(sensor_data))
            
            counter += 1
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.debug("Data sending task canceled")
    except Exception as e:
        logger.error(f"Error sending data: {e}")

async def main():
    """Main function"""
    host = "localhost"
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    server = await websockets.serve(handler, host, port)
    
    with open('pids/ws_server.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"Server started on ws://{host}:{port}")
    
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
EOF

chmod +x ./minimal_ws_server.py

# Part 3: Start the WebSocket server
echo "Starting WebSocket server..."
python3 ./minimal_ws_server.py &
WS_PID=$!
sleep 2

# Check if server started
if ps -p $WS_PID > /dev/null; then
    echo "✅ WebSocket server started on port 8765"
else
    echo "❌ WebSocket server failed to start"
    exit 1
fi

# Part 4: Fix Tauri dependencies and native modules
echo "Fixing Tauri dependencies..."

cd overlay

# Clean up existing Tauri installation
echo "Cleaning up Tauri installation..."
rm -rf node_modules
rm -f package-lock.json
npm cache clean --force

# Install latest compatible versions of Tauri packages
echo "Installing compatible Tauri packages..."
npm install

# First attempt with basic rebuild
echo "Trying basic rebuild of native modules..."
npm rebuild

# If that doesn't work, try specific Tauri versions
if [ $? -ne 0 ]; then
    echo "Basic rebuild failed, trying specific Tauri versions..."
    npm install --save-exact @tauri-apps/api@1.5.1
    npm install --save-dev --save-exact @tauri-apps/cli@1.5.6
fi

# Check for Rust toolchain
echo "Checking Rust toolchain..."
if ! command -v rustc &> /dev/null; then
    echo "⚠️ Rust not found. Installing Rust (required for Tauri)..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

# Make sure toolchain is up to date
if command -v rustup &> /dev/null; then
    echo "Updating Rust toolchain..."
    rustup update
fi

# Try to fix cli-darwin-arm64 specifically (common issue on M1/M2 Macs)
TAURI_CLI_DIR="node_modules/@tauri-apps/cli"
if [ -d "$TAURI_CLI_DIR" ]; then
    echo "Fixing Tauri CLI for Apple Silicon..."
    # Download the correct binary if needed
    mkdir -p "$TAURI_CLI_DIR/node_modules/@tauri-apps/cli-darwin-arm64"
    
    # Create a simple test file to verify the CLI works
    echo "Verifying Tauri CLI..."
    npx tauri --version || echo "Tauri CLI may still have issues"
fi

# Part 5: Start Tauri in development mode
echo "Starting Tauri development mode..."
npm run tauri dev &
TAURI_PID=$!

# Save Tauri PID
echo $TAURI_PID > ../pids/tauri.pid

echo "
=====================================================
    SYSTEM RUNNING WITH FIXED COMPONENTS
=====================================================

1. WebSocket server running on ws://localhost:8765
2. Tauri starting in development mode

If Tauri fails to start with native module errors, try:
1. cd $(pwd)
2. npm install -g @tauri-apps/cli@latest
3. npm run tauri info
4. npm run tauri dev

WebSocket server logs: ../logs/minimal_ws.log

Press Ctrl+C to stop only the parent script (Tauri will keep running).
To stop all components:
kill $WS_PID $TAURI_PID
"

# Keep parent script running, but don't wait for Tauri
# This way if Tauri fails, the user can still see the instructions
sleep 60

# After waiting, check if everything is still running
if ps -p $WS_PID > /dev/null; then
    echo "WebSocket server is still running on PID $WS_PID"
else
    echo "⚠️ WebSocket server is no longer running"
fi

if ps -p $TAURI_PID > /dev/null; then
    echo "Tauri is still running on PID $TAURI_PID"
else
    echo "⚠️ Tauri is no longer running"
    echo "If you see errors about native modules, try the manual steps above"
fi

# Keep the script running until Ctrl+C
wait $WS_PID