#!/bin/bash

echo "Starting fixed minimal backend system..."

# Stop any running services
pkill -f "python.*sensor" 2>/dev/null || true
pkill -f "python.*ws_server" 2>/dev/null || true
pkill -f "python.*memory_connector" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true
sleep 1

# Setup directories and PIDs
mkdir -p logs/memory
mkdir -p logs/sensors
mkdir -p pids
mkdir -p memory
mkdir -p cache/process_sensor
mkdir -p cache/file_sensor
mkdir -p cache/screen_sensor

# Clean up cache 
echo "{}" > memory/memory_state.json
echo "{}" > memory/last_context.json
echo "[]" > cache/process_sensor/process_cache.json
echo "[]" > cache/file_sensor/last_file.json

# 1. Start fixed WebSocket server with proper handler signature
echo "Starting WebSocket server..."
cat > ./simple_ws_server_fixed.py << 'EOF'
import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_websocket')

# Connected clients
connected_clients = set()

# IMPORTANT: Handler must accept websocket AND path parameters
async def handler(websocket, path):
    """WebSocket connection handler with proper signature"""
    client_id = id(websocket)
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected. Path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome", 
            "message": "Welcome to the Aiayer system!",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data.get('type', 'unknown')}")
                
                # Echo back with confirmation
                response = {
                    "type": "response",
                    "originalType": data.get("type", "unknown"),
                    "message": f"Server received: {data.get('message', 'No message')}",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection with client {client_id} closed: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients]
        )

async def heartbeat():
    """Send periodic heartbeat to clients"""
    while True:
        if connected_clients:
            heartbeat_msg = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "active_connections": len(connected_clients)
            }
            await broadcast(heartbeat_msg)
            logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds

async def main():
    """Main server function"""
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat())
    
    # Start server
    port = 8767
    server = await websockets.serve(handler, "localhost", port)
    logger.info(f"WebSocket server started on ws://localhost:{port}")
    
    # Save PID to file
    with open('pids/ws_server_8767.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Keep server running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
EOF

# Run the fixed WebSocket server
python simple_ws_server_fixed.py &
sleep 2

# Check if WebSocket server is running
if ps -p $(cat pids/ws_server_8767.pid 2>/dev/null) > /dev/null; then
    echo "✅ Fixed WebSocket server running on port 8767"
else
    echo "❌ WebSocket server failed to start"
    exit 1
fi

# 2. Start fixed memory connector
echo "Starting memory connector..."
cat > ./fixed_memory_connector.py << 'EOF'
import json
import os
import time
import logging
import sys
from datetime import datetime

# Setup directories
os.makedirs('logs/memory', exist_ok=True)
os.makedirs('memory', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_connector')

# Initialize memory state
def init_memory_state():
    """Initialize empty memory state"""
    return {
        "version": "1.0",
        "last_update": datetime.now().isoformat(),
        "context": {},
        "short_term": [],
        "long_term": []
    }

def save_memory_state(state):
    """Save memory state to file"""
    try:
        with open('memory/memory_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving memory state: {e}")
        return False

def load_memory_state():
    """Load memory state from file or initialize if not exists"""
    try:
        with open('memory/memory_state.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Memory state file issue: {e}, creating new state")
        new_state = init_memory_state()
        save_memory_state(new_state)
        return new_state

def run_memory_connector():
    """Main memory connector loop"""
    logger.info("Starting simple memory connector")
    
    # Save PID
    with open('pids/memory_connector.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Initial memory state
    memory_state = load_memory_state()
    
    # Monitor loop
    try:
        while True:
            # Update timestamp
            memory_state["last_update"] = datetime.now().isoformat()
            
            # Save updated state
            if save_memory_state(memory_state):
                logger.debug("Memory state updated")
            
            # Sleep to avoid high CPU usage
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Memory connector stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in memory connector: {e}")

if __name__ == "__main__":
    run_memory_connector()
EOF

# Run memory connector
python fixed_memory_connector.py &
sleep 1

# 3. Start overlay connector
echo "Starting overlay connector..."
cat > ./fixed_overlay_connector.py << 'EOF'
import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('overlay_connector')

# Save PID
with open('pids/overlay_connector.pid', 'w') as f:
    f.write(str(os.getpid()))

async def connect_to_server():
    """Connect to the WebSocket server and handle messages"""
    url = "ws://localhost:8767"
    logger.info(f"Attempting to connect to {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            logger.info(f"Connected to {url}")
            
            # Handle welcome message
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received from server: {data.get('type', 'unknown')} - {data.get('message', 'No message')}")
            
            # Send initialization message
            init_msg = {
                "type": "overlay_init",
                "message": "Overlay initialized and connected",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(init_msg))
            logger.info(f"Sent initialization message: {init_msg}")
            
            # Periodic test messages
            test_counter = 1
            while True:
                # Send test message
                test_msg = {
                    "type": "overlay_update",
                    "message": f"Periodic test message #{test_counter}",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(test_msg))
                logger.info(f"Sent test message #{test_counter}")
                
                # Receive response
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"Received response: {data}")
                
                test_counter += 1
                await asyncio.sleep(10)  # Wait 10 seconds between messages
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"Connection closed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

async def main():
    """Main function with retry logic"""
    retries = 0
    max_retries = 10
    retry_delay = 5
    
    while retries < max_retries:
        success = await connect_to_server()
        if success:
            break
            
        retries += 1
        logger.warning(f"Connection attempt {retries}/{max_retries} failed. Retrying in {retry_delay} seconds...")
        await asyncio.sleep(retry_delay)
    
    if retries >= max_retries:
        logger.error("Maximum retry attempts reached. Giving up.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Overlay connector stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
EOF

# Run overlay connector
python fixed_overlay_connector.py &
sleep 2

# 4. Check component status
echo "Checking component status..."
echo "WebSocket server: $(ps -p $(cat pids/ws_server_8767.pid 2>/dev/null) > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "Memory connector: $(ps -p $(cat pids/memory_connector.pid 2>/dev/null) > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "Overlay connector: $(ps -p $(cat pids/overlay_connector.pid 2>/dev/null) > /dev/null && echo '✅ Running' || echo '❌ Not running')"

echo "
System should now be running with:
1. WebSocket server on port 8767
2. Memory system with persistent state
3. Overlay client connected to WebSocket

Check logs in:
- WebSocket server: logs/fixed_ws.log
- Memory connector: logs/memory/connector.log
- Overlay connector: logs/overlay_connector.log

To stop the system:
kill \$(cat pids/ws_server_8767.pid) \$(cat pids/memory_connector.pid) \$(cat pids/overlay_connector.pid)
"