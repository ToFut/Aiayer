#!/bin/bash
# Fixed overlay startup script that ensures proper port configuration

echo "====================================================="
echo "    Starting Fixed Tauri Overlay System              "
echo "====================================================="

# Create required directories
mkdir -p logs/overlay
mkdir -p pids

# 1. First check if WebSocket port 8767 is available (this is the port the overlay expects)
if command -v nc &>/dev/null && nc -z localhost 8767 2>/dev/null; then
    echo "⚠️  Port 8767 is already in use. Stopping existing services..."
    pkill -f "python.*8767" 2>/dev/null || true
    sleep 1
fi

# 2. Create WebSocket server on port 8767 (the port the overlay expects)
echo "Creating WebSocket server on port 8767..."
cat > ./fixed_ws_server_8767.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs/overlay', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay/ws_server_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ws_server_8767')

# Track connected clients
connected_clients = set()

# Handle WebSocket connections
async def handler(websocket, path):
    """Handler for websocket connections"""
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
                if data.get('type') == 'register':
                    logger.info(f"Client registered: {data.get('payload', {})}")
                    
                    # Send connection status message
                    await websocket.send(json.dumps({
                        "type": "connection_status",
                        "payload": {
                            "state": "connected",
                            "server": "ws_server_8767",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                elif data.get('type') == 'user_interaction':
                    # Handle user queries
                    payload = data.get('payload', {})
                    if payload.get('type') == 'query':
                        query = payload.get('query', '')
                        logger.info(f"User query: {query}")
                        
                        # Send mock response
                        await websocket.send(json.dumps({
                            "type": "query_response",
                            "response": f"You asked: {query}. This is a sample response from the WebSocket server.",
                            "timestamp": datetime.now().isoformat()
                        }))
                
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
    except Exception as e:
        logger.error(f"Error in handler: {e}")
    finally:
        if websocket in connected_clients:
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
                if websocket.open:
                    await websocket.send(json.dumps(context_data))
                    logger.debug(f"Sent context update to {client_id}")
            except Exception as e:
                logger.error(f"Error sending context to {client_id}: {e}")
                raise
                
            # Send every 5 seconds
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.debug(f"Context updates for {client_id} stopped")
        raise

async def main():
    # Bind to localhost on port 8767
    port = 8767
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket server on {host}:{port}")
    async with websockets.serve(handler, host, port):
        # Save PID
        with open('pids/ws_server_8767.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        
        # Keep running forever
        await asyncio.Future()

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs/overlay", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
EOF

# Make script executable
chmod +x ./fixed_ws_server_8767.py

# 3. Launch the WebSocket server on port 8767
echo "Starting WebSocket server on port 8767..."
python3 ./fixed_ws_server_8767.py &
WS_PID=$!
echo $WS_PID > pids/ws_server_8767.pid
sleep 2

# 4. Check if WebSocket server is running
if ps -p $WS_PID > /dev/null; then
    echo "✅ WebSocket server started successfully on port 8767"
else
    echo "❌ WebSocket server failed to start!"
    exit 1
fi

# 5. Now start Tauri in a separate terminal window
echo "Starting Tauri in a new terminal window..."
cat > /tmp/start_tauri.sh << 'EOF'
#!/bin/bash
echo "Starting Tauri development server..."
cd "$(dirname "$0")"
cd ./overlay

# Make sure dependencies are installed
echo "Checking npm dependencies..."
if [ ! -d "node_modules" ] || [ ! -d "node_modules/vite" ]; then
    echo "Installing npm dependencies (this may take a minute)..."
    npm install
fi

# Run Tauri
echo "Starting Tauri..."
npm run tauri dev
EOF

chmod +x /tmp/start_tauri.sh

# Start a new terminal to run Tauri
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd \"'$PWD'\" && /tmp/start_tauri.sh"'
else
    # Linux and others - try to use x-terminal-emulator if available
    if command -v x-terminal-emulator >/dev/null; then
        x-terminal-emulator -e "bash -c '/tmp/start_tauri.sh; exec bash'" &
    elif command -v gnome-terminal >/dev/null; then
        gnome-terminal -- bash -c "/tmp/start_tauri.sh; exec bash" &
    elif command -v xterm >/dev/null; then
        xterm -e "bash -c '/tmp/start_tauri.sh; exec bash'" &
    else
        echo "⚠️ Could not determine how to open a new terminal window."
        echo "Please open a new terminal window and run:"
        echo "cd $PWD/overlay && npm run tauri dev"
    fi
fi

echo "
=====================================================
    Aiayer System Running with Tauri Overlay
=====================================================

1. WebSocket server running on ws://localhost:8767
2. Tauri overlay should be starting in a new terminal window

IMPORTANT INSTRUCTIONS TO SEE THE OVERLAY:

1. The overlay uses transparency and might be difficult to see initially
2. Look for a small eye icon (👁️) widget somewhere on your screen 
3. Try using the keyboard shortcut Cmd+Shift+A (⌘⇧A) to toggle the chat
4. If you still don't see it, the eye widget is initially positioned at:
   x=20, y=20 (top-left corner)

If the Tauri window doesn't open automatically, run:
cd $PWD/overlay && npm install && npm run tauri dev

To monitor logs:
- WebSocket server: tail -f logs/overlay/ws_server_8767.log

To stop all components:
- kill $WS_PID 
"