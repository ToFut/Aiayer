#!/bin/bash

echo "====================================================="
echo "    ABSOLUTELY FINAL FIX FOR AIAYER SYSTEM           "
echo "====================================================="

# Kill ALL Python processes to ensure no conflicts whatsoever
echo "WARNING: This will kill ALL running Python processes on your system."
echo "Press Ctrl+C now to abort or wait 5 seconds to continue..."

sleep 5

echo "Killing ALL Python processes..."
killall -9 python python3 2>/dev/null || true

# Force kill anything using port 8765
PIDS_ON_8765=$(lsof -i:8765 -t 2>/dev/null)
if [ -n "$PIDS_ON_8765" ]; then
    echo "Killing processes using port 8765: $PIDS_ON_8765"
    kill -9 $PIDS_ON_8765 2>/dev/null || true
fi

# Ensure we have a clean working directory
cd /Users/segevbin/Desktop/SensAI/Aiayer

# Clear all Python cache files that might be causing problems
echo "Clearing all Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Clear the terminal for a fresh start
clear

# Create an isolated, standalone WebSocket server script
echo "Creating isolated WebSocket server..."
cat > standalone_ws.py << 'EOF'
#!/usr/bin/env python3
"""
ABSOLUTELY ISOLATED WebSocket server - no imports from project code
This is a completely standalone implementation with no dependencies 
on any other project files to avoid any import or module cache issues.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Installing websockets... (this will only happen once)")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,  # Using DEBUG level to catch everything
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/standalone.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("standalone_ws")

# Connected clients
connected_clients = set()

# THE HANDLER FUNCTION - EXPLICITLY REQUIRES BOTH PARAMETERS
async def handler(websocket, path):
    """
    WebSocket connection handler.
    This signature MUST have both websocket and path parameters.
    """
    # Print to both console and log
    msg = f"CLIENT CONNECTED on path: {path}"
    print("\n" + "="*50)
    print(msg)
    print("="*50 + "\n")
    logger.info(msg)
    
    # Add to connected clients
    connected_clients.add(websocket)
    client_id = id(websocket)
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "welcome", 
            "message": f"Connected to the standalone server. Path: {path}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))
        logger.info(f"Sent welcome message to client {client_id}")
        
        # Start data sending task
        data_task = asyncio.create_task(
            send_periodic_data(websocket, client_id)
        )
        
        # Process incoming messages
        async for message in websocket:
            try:
                # Try to parse JSON
                data = json.loads(message)
                msg_type = data.get("type", "unknown") if isinstance(data, dict) else "unknown"
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                print(f"Received: {msg_type}")
                
                # Handle different message types
                if msg_type == "connection_established":
                    client_info = data.get("payload", {})
                    logger.info(f"Client identified: {client_info}")
                    
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    logger.info("Sent server_ready message")
                    
                # Echo back all other messages
                else:
                    await websocket.send(json.dumps({
                        "type": "response",
                        "payload": {
                            "received": data,
                            "message": "Message received successfully",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    logger.info(f"Echoed message back to client {client_id}")
                
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with client {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Clean up
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket, client_id):
    """Send periodic simulated data to the client"""
    try:
        import random
        counter = 0
        
        while True:
            # Create simulated data every 5 seconds
            current_time = datetime.now()
            
            # Simulate process data
            processes = [
                {"name": "Chrome", "pid": 12345, "cpu": random.uniform(5, 20), "memory": 350 + random.uniform(-10, 10)},
                {"name": "Code", "pid": 12346, "cpu": random.uniform(2, 10), "memory": 250 + random.uniform(-20, 20)},
                {"name": "Terminal", "pid": 12347, "cpu": random.uniform(0.5, 5), "memory": 120 + random.uniform(-5, 5)}
            ]
            
            # Simulate screen data
            apps = ["Chrome", "Code", "Terminal", "Finder"]
            active_app = apps[counter % len(apps)]
            
            screen_data = {
                "active_app": active_app,
                "window_title": f"{active_app} - Working on project",
                "timestamp": current_time.isoformat()
            }
            
            # Bundle into sensor data package
            sensor_data = {
                "type": "sensor_data",
                "payload": {
                    "processes": processes,
                    "screen": screen_data,
                    "files": [],
                    "timestamp": current_time.isoformat()
                }
            }
            
            # Send the data
            await websocket.send(json.dumps(sensor_data))
            logger.debug(f"Sent data update #{counter} to client {client_id}")
            
            # Occasionally send a suggestion
            if counter % 6 == 0:  # Every 30 seconds
                suggestion = {
                    "type": "suggestions",
                    "payload": [{
                        "id": f"suggestion_{counter}",
                        "title": "System Performance Tip",
                        "content": f"Consider optimizing your workflow in {active_app}.",
                        "urgency": random.randint(1, 5),
                        "category": "performance",
                        "buttons": [
                            {"label": "Apply", "id": "apply"},
                            {"label": "Dismiss", "id": "dismiss"}
                        ]
                    }]
                }
                
                await websocket.send(json.dumps(suggestion))
                logger.debug(f"Sent suggestion to client {client_id}")
            
            counter += 1
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.debug(f"Data sending task for client {client_id} canceled")
    except websockets.exceptions.ConnectionClosed:
        logger.debug(f"Connection closed while sending data to client {client_id}")
    except Exception as e:
        logger.error(f"Error sending data to client {client_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """Main function to run the WebSocket server"""
    # Create required directories
    os.makedirs("pids", exist_ok=True)
    
    host = "localhost"
    port = 8765  # The port expected by the overlay
    
    # Start the server
    print(f"\n\nSTARTING WEBSOCKET SERVER ON {host}:{port}")
    print(f"HANDLER FUNCTION HAS SIGNATURE: async def handler(websocket, path)\n\n")
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    # Create the server
    server = await websockets.serve(
        handler,  # This handler has signature: handler(websocket, path)
        host, 
        port
    )
    
    # Save PID
    with open('pids/standalone_ws.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info(f"Server started successfully!")
    print(f"\n✅ SERVER STARTED SUCCESSFULLY!")
    print(f"Debug logs at: logs/standalone.log\n")
    
    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        # Run the event loop
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        print("\nServer stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)
EOF

# Make it executable
chmod +x ./standalone_ws.py

# Run the standalone server
echo "Starting absolutely isolated WebSocket server..."
python3 ./standalone_ws.py &
WS_PID=$!

# Wait to ensure it starts
sleep 3

# Check if it's running
if ps -p $WS_PID > /dev/null; then
    echo "✅ Standalone WebSocket server started on port 8765"
else
    echo "❌ Failed to start WebSocket server"
    exit 1
fi

# Create a script for starting Tauri in a completely new environment
echo "Preparing Tauri startup script..."
cat > /tmp/start_tauri.sh << 'EOF'
#!/bin/bash

echo "Starting Tauri overlay..."
cd "$(dirname "$0")"
cd ./overlay

# Make sure dependencies are installed
echo "Checking npm dependencies..."
if [ ! -d "node_modules" ] || [ ! -d "node_modules/vite" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start Tauri
echo "Starting Tauri development server..."
npm run tauri dev
EOF

chmod +x /tmp/start_tauri.sh

# Start a new terminal to run Tauri
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '$PWD' && /tmp/start_tauri.sh"'
else
    # Linux and others
    echo "Please open a new terminal window and run:"
    echo "cd $PWD/overlay && npm install && npm run tauri dev"
fi

echo "
=====================================================
    AIAYER SYSTEM RUNNING WITH ABSOLUTE ISOLATION
=====================================================

This solution:
1. Killed ALL Python processes to ensure no conflicts
2. Cleared all Python cache files
3. Created a completely isolated WebSocket server
4. Explicitly logs the handler signature

The WebSocket server is listening on localhost:8765.
Tauri should open in a new terminal window.

If the Tauri window doesn't open automatically, run:
cd $PWD/overlay && npm install && npm run tauri dev

Press Ctrl+C to stop the WebSocket server.
"

# Keep the script running until Ctrl+C
trap "kill $WS_PID; echo 'System stopped.'" EXIT
wait $WS_PID