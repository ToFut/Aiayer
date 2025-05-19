#!/bin/bash

echo "====================================================="
echo "    Starting Complete Aiayer System with Overlay     "
echo "====================================================="

# 1. Stop any existing processes
echo "Stopping any running services..."
pkill -f "python.*sensor" 2>/dev/null || true
pkill -f "python.*ws_server" 2>/dev/null || true
pkill -f "python.*memory" 2>/dev/null || true
pkill -f "python.*overlay" 2>/dev/null || true
sleep 1

# 2. Create required directories
echo "Setting up directories..."
mkdir -p logs/memory
mkdir -p logs/sensors
mkdir -p pids
mkdir -p memory
mkdir -p cache/process_sensor
mkdir -p cache/file_sensor
mkdir -p cache/screen_sensor

# 3. Initialize essential cache files
echo "Initializing cache files..."
echo "{}" > memory/memory_state.json
echo "{}" > memory/last_context.json
echo "[]" > cache/process_sensor/process_cache.json
echo "[]" > cache/file_sensor/last_file.json
echo "{}" > cache/screen_sensor/screen_cache.json

# 4. Create WebSocket server to connect overlay and backend
echo "Creating WebSocket bridge..."
cat > ./bridge_server.py << 'EOF'
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
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bridge_server')

# Track connected clients
connected_clients = set()
sensor_data = {
    "processes": [],
    "screen": {},
    "files": []
}

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
        
        # Send initial sensor data (if we have any)
        if any(sensor_data.values()):
            await websocket.send(json.dumps({
                "type": "sensor_data",
                "payload": sensor_data
            }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle specific message types
                if msg_type == 'connection_established':
                    logger.info(f"Overlay client initialized: {data.get('payload', {})}")
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "capabilities": ["context_tracking", "suggestions", "screen_capture"]
                        }
                    }))
                elif msg_type == 'process_data':
                    # Store process data from sensor
                    sensor_data["processes"] = data.get('payload', [])
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data
                    })
                elif msg_type == 'screen_data':
                    # Store screen data from sensor
                    sensor_data["screen"] = data.get('payload', {})
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data
                    })
                elif msg_type == 'file_data':
                    # Store file data from sensor
                    sensor_data["files"] = data.get('payload', [])
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data
                    })
                else:
                    # Default echo response
                    response = {
                        "type": "response",
                        "payload": {
                            "message": f"Received {msg_type} message",
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
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients],
            return_exceptions=True
        )
        logger.debug(f"Broadcast sent to {len(connected_clients)} clients")

async def main():
    # Bind to localhost on port 8765 (for overlay connections)
    port = 8765
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket bridge server on {host}:{port}")
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    with open('pids/bridge_server.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"WebSocket bridge server started on ws://{host}:{port}")
    
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

chmod +x ./bridge_server.py

# 5. Create a minimal process sensor that connects to the bridge
echo "Creating minimal process sensor..."
cat > ./minimal_process_sensor.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import psutil
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('process_sensor')

async def send_process_data():
    """Collect and send process data to the bridge server"""
    uri = "ws://localhost:8765"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to bridge server at {uri}")
                
                # Process initial welcome message
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"Received from server: {data.get('type')}")
                
                # Send identification
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "client": "process_sensor",
                        "version": "0.1.0"
                    }
                }))
                
                # Main data collection loop
                while True:
                    try:
                        # Collect process data
                        processes = []
                        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                            try:
                                # Get process info
                                proc_info = proc.info
                                memory_mb = proc_info['memory_info'].rss / (1024 * 1024) if proc_info['memory_info'] else 0
                                
                                processes.append({
                                    "pid": proc_info['pid'],
                                    "name": proc_info['name'],
                                    "cpu": proc_info['cpu_percent'],
                                    "memory": round(memory_mb, 1)
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                pass
                        
                        # Sort by CPU usage (descending)
                        processes.sort(key=lambda x: x['cpu'], reverse=True)
                        # Take top 10 processes
                        top_processes = processes[:10]
                        
                        # Send to bridge server
                        await websocket.send(json.dumps({
                            "type": "process_data",
                            "payload": top_processes,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        # Wait before next collection
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        logger.error(f"Error in data collection: {e}")
                        await asyncio.sleep(5)
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection to bridge server failed: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/process_sensor.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info("Starting minimal process sensor...")
    asyncio.run(send_process_data())
EOF

chmod +x ./minimal_process_sensor.py

# 6. Create a minimal screen sensor
echo "Creating minimal screen sensor..."
cat > ./minimal_screen_sensor.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import psutil
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('screen_sensor')

async def send_screen_data():
    """Collect and send screen data to the bridge server"""
    uri = "ws://localhost:8765"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to bridge server at {uri}")
                
                # Process initial welcome message
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"Received from server: {data.get('type')}")
                
                # Send identification
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "client": "screen_sensor",
                        "version": "0.1.0"
                    }
                }))
                
                # Main data collection loop
                window_titles = [
                    "Visual Studio Code - project.py",
                    "Terminal - bash",
                    "Chrome - GitHub",
                    "Finder - Documents",
                    "Safari - AI Research",
                    "Slack - General"
                ]
                title_index = 0
                
                while True:
                    try:
                        # Create simulated screen data
                        # In a real implementation, this would capture actual screen info
                        screen_data = {
                            "window_title": window_titles[title_index],
                            "active_app": window_titles[title_index].split(" - ")[0],
                            "system_stats": {
                                "cpu": psutil.cpu_percent(),
                                "memory": psutil.virtual_memory().percent,
                                "battery": psutil.sensors_battery().percent if psutil.sensors_battery() else None
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Rotate through sample window titles
                        title_index = (title_index + 1) % len(window_titles)
                        
                        # Send to bridge server
                        await websocket.send(json.dumps({
                            "type": "screen_data",
                            "payload": screen_data,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        # Wait before next collection
                        await asyncio.sleep(10)
                        
                    except Exception as e:
                        logger.error(f"Error in data collection: {e}")
                        await asyncio.sleep(5)
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection to bridge server failed: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/screen_sensor.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info("Starting minimal screen sensor...")
    asyncio.run(send_screen_data())
EOF

chmod +x ./minimal_screen_sensor.py

# 7. Create a simple memory system
echo "Creating minimal memory system..."
cat > ./minimal_memory.py << 'EOF'
#!/usr/bin/env python3
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_system')

class MinimalMemory:
    def __init__(self, memory_file="memory/memory_state.json"):
        self.memory_file = memory_file
        self.memory_state = self.load_memory()
        
    def load_memory(self):
        """Load memory state from file or create new if it doesn't exist"""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create new memory state
            logger.info("Creating new memory state")
            return {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": {},
                "short_term": [],
                "long_term": []
            }
    
    def save_memory(self):
        """Save memory state to file"""
        try:
            # Update timestamp
            self.memory_state["last_update"] = datetime.now().isoformat()
            
            # Save to file
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory_state, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving memory state: {e}")
            return False
    
    def run(self):
        """Main memory system loop"""
        logger.info("Starting minimal memory system")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/memory.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            while True:
                # Update memory periodically
                self.save_memory()
                
                # Log status
                logger.debug(f"Memory state updated - {len(self.memory_state['short_term'])} short term memories, {len(self.memory_state['long_term'])} long term memories")
                
                # Sleep to avoid high CPU usage
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Memory system stopped by user")
            self.save_memory()
        except Exception as e:
            logger.error(f"Error in memory system: {e}")
            self.save_memory()

if __name__ == "__main__":
    memory = MinimalMemory()
    memory.run()
EOF

chmod +x ./minimal_memory.py

# 8. Start all backend components
echo "Starting backend components..."

# Start bridge server
echo "Starting WebSocket bridge server..."
python3 ./bridge_server.py &
sleep 2

# Check if bridge server is running
if pgrep -f "python.*bridge_server.py" > /dev/null; then
    echo "✅ Bridge server started"
else
    echo "❌ Bridge server failed to start"
    exit 1
fi

# Start memory system
echo "Starting memory system..."
python3 ./minimal_memory.py &
sleep 1

# Start process sensor
echo "Starting process sensor..."
python3 ./minimal_process_sensor.py &
sleep 1

# Start screen sensor
echo "Starting screen sensor..."
python3 ./minimal_screen_sensor.py &
sleep 1

# 9. Start Tauri overlay in a separate terminal
echo "Starting Tauri overlay in a new terminal window..."
cat > /tmp/start_tauri.sh << 'EOF'
#!/bin/bash
echo "Starting Tauri overlay..."
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
    osascript -e 'tell app "Terminal" to do script "cd '$PWD' && /tmp/start_tauri.sh"'
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
        echo "cd $PWD/overlay && npm install && npm run tauri dev"
    fi
fi

echo "
=====================================================
    Complete Aiayer System Running
=====================================================

BACKEND COMPONENTS:
1. WebSocket bridge server on port 8765
2. Process sensor collecting real-time process data
3. Screen sensor simulating screen activity
4. Memory system for context persistence

FRONTEND:
- Tauri overlay should be starting in a new terminal window

If the Tauri window doesn't open automatically, run:
cd $PWD/overlay && npm install && npm run tauri dev

LOGS:
- Bridge server: logs/bridge_server.log
- Process sensor: logs/sensors/process_sensor.log
- Screen sensor: logs/sensors/screen_sensor.log
- Memory system: logs/memory/memory.log

TO STOP THE SYSTEM:
pkill -f 'python.*bridge_server.py' && pkill -f 'python.*_sensor.py' && pkill -f 'python.*memory.py'
"

# Write instructions to a file for easy reference
echo "If you need to manually start Tauri, run these commands:
cd $PWD/overlay
npm install
npm run tauri dev

To stop the backend system:
pkill -f 'python.*bridge_server.py' && pkill -f 'python.*_sensor.py' && pkill -f 'python.*memory.py'
" > start_system_manual.txt

# Keep the script running
echo "Press Ctrl+C to stop all backend components"
wait