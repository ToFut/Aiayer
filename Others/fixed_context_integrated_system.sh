#!/bin/bash
# fixed_context_integrated_system.sh
# Properly connects sensors to bridge server and memory system for context integration

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored text
print_colored() {
    color=$1
    text=$2
    
    case $color in
        "green") echo -e "${GREEN}$text${NC}" ;;
        "yellow") echo -e "${YELLOW}$text${NC}" ;;
        "blue") echo -e "${BLUE}$text${NC}" ;;
        "red") echo -e "${RED}$text${NC}" ;;
        *) echo "$text" ;;
    esac
}

# Create necessary directories
print_colored "blue" "Creating necessary directories..."
mkdir -p logs/sensors/screen_sensor
mkdir -p logs/sensors/process_sensor
mkdir -p logs/sensors/file_sensor
mkdir -p logs/memory
mkdir -p logs/bridge
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p cache/file_sensor
mkdir -p memory/screen_data

# Function to kill process using a port
kill_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        local pid=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            print_colored "yellow" "Killing process $pid using port $port"
            kill -9 $pid 2>/dev/null || true
            sleep 1
        fi
    fi
}

# Function to kill processes by keyword
kill_process() {
    process_name=$1
    print_colored "yellow" "Stopping ${process_name} processes..."
    pids=$(ps aux | grep -i "${process_name}" | grep -v grep | awk '{print $2}')
    if [ -n "$pids" ]; then
        print_colored "yellow" "Killing processes: $pids"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || print_colored "yellow" "Process $pid already gone"
        done
        print_colored "green" "${process_name} processes stopped"
    else
        print_colored "blue" "No ${process_name} processes found running"
    fi
}

# Stop any existing processes
print_colored "yellow" "Cleaning up any existing processes..."
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        name=$(basename "$pid_file" .pid)
        print_colored "yellow" "Stopping previous $name (PID: $pid)..."
        kill -9 $pid 2>/dev/null || true
        rm -f "$pid_file"
    fi
done

# Kill processes by name
kill_process "sensor"
kill_process "connect_sensor_to_memory"
kill_process "memory_connector"
kill_process "ws_server"
kill_process "websocket"
kill_process "minimal_ws"
kill_process "bridge_server"

# Clean up ports
print_colored "yellow" "Cleaning up ports..."
kill_port 8765  # WebSocket server port
kill_port 8766  # Bridge server port
kill_port 8767  # Backend server port
sleep 2

# Initialize essential files
print_colored "blue" "Initializing essential files..."
timestamp=$(date +%Y%m%d_%H%M%S)

# Initialize process cache with proper structure
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
if [ -f "cache/screen_sensor/screen_cache.json" ] && [ -s "cache/screen_sensor/screen_cache.json" ]; then
    cp "cache/screen_sensor/screen_cache.json" "cache/screen_sensor/screen_cache.json.bak_${timestamp}"
fi
echo '{
    "timestamp": '$(date +%s)',
    "screen_text": "",
    "has_images": false,
    "has_videos": false
}' > "cache/screen_sensor/screen_cache.json"

# Initialize last_screen.json
echo '{
    "timestamp": '$(date +%s)',
    "screen_text": "",
    "has_images": false,
    "has_videos": false
}' > "cache/screen_sensor/last_screen.json"

# Initialize memory state
if [ ! -f "memory/memory_state.json" ] || [ ! -s "memory/memory_state.json" ]; then
    echo '{
        "version": "1.0",
        "last_update": "'$(date -Iseconds)'",
        "context": {},
        "short_term": [],
        "long_term": []
    }' > "memory/memory_state.json"
fi

# Initialize last_context.json
echo '{
    "timestamp": '$(date +%s)',
    "active_window": "",
    "active_app": "",
    "active_apps": [],
    "window_history": [],
    "screen_text": ""
}' > "memory/last_context.json"

print_colored "green" "Cache files prepared"

# Function to start a service and capture its PID
start_service() {
    service_name=$1
    command=$2
    log_file=$3
    pid_file=$4
    max_retries=${5:-3}  # Default to 3 retries
    
    print_colored "blue" "Starting $service_name..."
    mkdir -p $(dirname "$log_file")
    
    for ((i=1; i<=max_retries; i++)); do
        eval "$command > $log_file 2>&1 &"
        pid=$!
        echo $pid > $pid_file
        
        # Wait briefly to check if process remains running
        sleep 2
        if ps -p $pid > /dev/null; then
            print_colored "green" "✅ $service_name started with PID: $pid"
            return 0
        else
            print_colored "yellow" "⚠️ Attempt $i/$max_retries failed for $service_name"
            if [ $i -lt $max_retries ]; then
                sleep 2
            fi
        fi
    done
    
    print_colored "red" "❌ $service_name failed to start after $max_retries attempts. Check logs at $log_file"
    return 1
}

# Create bridge server connector if needed
if [ ! -f "fixed_bridge_connector.py" ]; then
    print_colored "blue" "Creating bridge connector script..."
    cat > fixed_bridge_connector.py << 'EOF'
#!/usr/bin/env python3
"""
Fixed Bridge Connector

Acts as a bridge between sensors, memory system, and LLM services.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
from datetime import datetime

# Setup logging
os.makedirs('logs/bridge', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge/connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bridge_connector')

# WebSocket configuration
WS_PORT = 8766
HOST = "0.0.0.0"

# Track connected clients
connected_clients = set()
sensor_clients = {}
memory_clients = set()
llm_clients = set()
ui_clients = set()

# Buffer for sensor data
sensor_data = {
    'screen': {},
    'process': {},
    'file': {}
}

async def broadcast_to_memory(data):
    """Broadcast data to all memory clients"""
    if not memory_clients:
        logger.warning("No memory clients connected to receive data")
        return
    
    try:
        message = json.dumps(data)
        logger.debug(f"Broadcasting to {len(memory_clients)} memory clients")
        await asyncio.gather(
            *[client.send(message) for client in memory_clients],
            return_exceptions=True
        )
    except Exception as e:
        logger.error(f"Error broadcasting to memory: {e}")

async def handle_client(websocket, path):
    """Handle WebSocket client connections"""
    client_type = None
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to bridge server",
            "timestamp": datetime.now().isoformat()
        }))
        
        logger.info(f"New client connected: {client_id}")
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                # Handle registration messages
                if msg_type == 'register' or msg_type == 'connection_established':
                    # Extract client type
                    if msg_type == 'register':
                        client_type = data.get('client_type', 'unknown').lower()
                        sensor_type = data.get('sensor_type', '').lower()
                    else:  # connection_established
                        client_type = data.get('payload', {}).get('client', 'unknown').lower()
                        sensor_type = ''
                    
                    # Register client
                    if client_type == 'sensor':
                        if sensor_type:
                            sensor_clients[websocket] = sensor_type
                            logger.info(f"Registered {sensor_type} sensor: {client_id}")
                        else:
                            logger.warning(f"Sensor client without type: {client_id}")
                            sensor_clients[websocket] = 'unknown'
                    elif client_type == 'memory':
                        memory_clients.add(websocket)
                        logger.info(f"Registered memory client: {client_id}")
                    elif client_type == 'llm':
                        llm_clients.add(websocket)
                        logger.info(f"Registered LLM client: {client_id}")
                    elif client_type in ['ui', 'overlay']:
                        ui_clients.add(websocket)
                        logger.info(f"Registered UI client: {client_id}")
                    else:
                        logger.info(f"Registered unknown client type: {client_id} as {client_type}")
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "type": "registration_confirmed",
                        "client_type": client_type,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Handle sensor data
                elif msg_type == 'sensor_data':
                    sensor_type = data.get('sensor_type', '')
                    payload = data.get('payload', {})
                    
                    if sensor_type and payload:
                        # Store in the appropriate buffer
                        sensor_data[sensor_type] = payload
                        
                        # Forward to memory clients
                        await broadcast_to_memory({
                            "type": "sensor_data",
                            "sensor_type": sensor_type,
                            "payload": payload,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Send acknowledgment
                        await websocket.send(json.dumps({
                            "type": "ack",
                            "message": f"Processed {sensor_type} sensor data",
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        logger.info(f"Processed {sensor_type} sensor data from {client_id}")
                    else:
                        logger.warning(f"Invalid sensor data from {client_id}")
                
                # Handle ping messages
                elif msg_type == 'ping':
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Handle other message types
                else:
                    logger.debug(f"Received {msg_type} message from {client_id}")
                    
                    # Echo back for unknown message types
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "original_type": msg_type,
                        "timestamp": datetime.now().isoformat()
                    }))
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        # Clean up client registration
        connected_clients.discard(websocket)
        if websocket in sensor_clients:
            del sensor_clients[websocket]
        memory_clients.discard(websocket)
        llm_clients.discard(websocket)
        ui_clients.discard(websocket)
        logger.info(f"Client removed: {client_id}")

async def status_broadcaster():
    """Periodically broadcast status to all clients"""
    while True:
        try:
            if connected_clients:
                # Prepare status message
                status = {
                    "type": "status_update",
                    "clients": {
                        "total": len(connected_clients),
                        "sensors": len(sensor_clients),
                        "memory": len(memory_clients),
                        "llm": len(llm_clients),
                        "ui": len(ui_clients)
                    },
                    "sensor_data": {
                        k: bool(v) for k, v in sensor_data.items()
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                # Broadcast to all clients
                message = json.dumps(status)
                await asyncio.gather(
                    *[client.send(message) for client in connected_clients],
                    return_exceptions=True
                )
                
                logger.debug(f"Status broadcast sent to {len(connected_clients)} clients")
            
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in status broadcaster: {e}")
            await asyncio.sleep(10)  # Shorter sleep on error

async def main():
    """Main function to start the bridge server"""
    try:
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/bridge_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"Starting bridge server on {HOST}:{WS_PORT}")
        
        # Start the WebSocket server
        server = await websockets.serve(
            handle_client, 
            HOST, 
            WS_PORT,
            ping_interval=30,
            ping_timeout=60,
            close_timeout=10
        )
        
        # Start the status broadcaster
        asyncio.create_task(status_broadcaster())
        
        logger.info(f"Bridge server running on ws://{HOST}:{WS_PORT}")
        await server.wait_closed()
    
    except Exception as e:
        logger.error(f"Error starting bridge server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bridge server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
EOF
    chmod +x fixed_bridge_connector.py
fi

# Create enhanced memory connector if needed
if [ ! -f "fixed_memory_connector.py" ]; then
    print_colored "blue" "Creating memory connector script..."
    cat > fixed_memory_connector.py << 'EOF'
#!/usr/bin/env python3
"""
Fixed Memory Connector

Connects to the bridge server to receive sensor data and updates memory system.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_connector')

# Bridge server configuration
BRIDGE_WS_URI = "ws://localhost:8766"

# Memory files
MEMORY_STATE_FILE = "memory/memory_state.json"
CONTEXT_FILE = "memory/last_context.json"

async def update_memory_from_sensor_data(sensor_type, data):
    """Update memory system with sensor data"""
    try:
        logger.debug(f"Updating memory with {sensor_type} data")
        
        # Load current memory state
        memory_state = load_memory_state()
        
        # Update context
        if "context" not in memory_state:
            memory_state["context"] = {}
        
        # Create sensor data section if needed
        if "sensor_data" not in memory_state["context"]:
            memory_state["context"]["sensor_data"] = {
                "screen": {},
                "process": {},
                "file": {}
            }
        
        # Update appropriate sensor data
        memory_state["context"]["sensor_data"][sensor_type] = data
        memory_state["last_update"] = datetime.now().isoformat()
        
        # Save updated memory state
        save_memory_state(memory_state)
        
        # Update last_context.json for external components
        update_context_file(sensor_type, data)
        
        logger.info(f"Memory updated with {sensor_type} data")
        return True
    except Exception as e:
        logger.error(f"Error updating memory: {e}")
        return False

def load_memory_state():
    """Load memory state from file"""
    try:
        if os.path.exists(MEMORY_STATE_FILE):
            with open(MEMORY_STATE_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default memory state
            state = {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": {
                    "sensor_data": {
                        "screen": {},
                        "process": {},
                        "file": {}
                    }
                },
                "short_term": [],
                "long_term": []
            }
            save_memory_state(state)
            return state
    except Exception as e:
        logger.error(f"Error loading memory state: {e}")
        # Return default state on error
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
        with open(MEMORY_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        logger.debug("Memory state saved")
        return True
    except Exception as e:
        logger.error(f"Error saving memory state: {e}")
        return False

def update_context_file(sensor_type, data):
    """Update last_context.json file with sensor data"""
    try:
        # Load current context
        context = {}
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r') as f:
                context = json.load(f)
        
        # Update timestamp
        context["timestamp"] = int(time.time())
        
        # Update based on sensor type
        if sensor_type == "process":
            context["active_window"] = data.get("active_window", "")
            context["active_app"] = data.get("active_app", "")
            context["active_apps"] = data.get("active_apps", [])
            context["window_history"] = data.get("window_history", [])
        elif sensor_type == "screen":
            context["screen_text"] = data.get("screen_text", "")
        
        # Save updated context
        with open(CONTEXT_FILE, 'w') as f:
            json.dump(context, f, indent=2)
        
        logger.info(f"✅ Updated last_context.json with {sensor_type} data")
        return True
    except Exception as e:
        logger.error(f"Error updating context file: {e}")
        return False

async def connect_to_bridge():
    """Connect to the bridge server and process data"""
    retry_delay = 5  # seconds
    
    while True:
        try:
            logger.info(f"Connecting to bridge server at {BRIDGE_WS_URI}")
            
            async with websockets.connect(BRIDGE_WS_URI) as websocket:
                logger.info("Connected to bridge server")
                
                # Register as a memory client
                await websocket.send(json.dumps({
                    "type": "register",
                    "client_type": "memory",
                    "version": "1.0.0",
                    "capabilities": ["context_storage", "memory_management"]
                }))
                
                # Wait for registration confirmation
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("type") == "registration_confirmed":
                    logger.info("Registration confirmed by bridge server")
                else:
                    logger.warning(f"Unexpected registration response: {data.get('type')}")
                
                # Process incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")
                        
                        if msg_type == "sensor_data":
                            # Extract sensor data
                            sensor_type = data.get("sensor_type", "")
                            payload = data.get("payload", {})
                            
                            if sensor_type and payload:
                                # Update memory with this data
                                await update_memory_from_sensor_data(sensor_type, payload)
                            else:
                                logger.warning("Received invalid sensor data")
                        
                        elif msg_type == "pong":
                            # Heartbeat response
                            logger.debug("Received heartbeat from bridge server")
                        
                        else:
                            logger.debug(f"Received message type: {msg_type}")
                        
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON received from bridge")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection to bridge server lost: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)

async def heartbeat_task():
    """Task to save memory state periodically"""
    while True:
        try:
            # Load and save memory state to keep it fresh
            memory_state = load_memory_state()
            memory_state["last_update"] = datetime.now().isoformat()
            save_memory_state(memory_state)
            
            logger.info("✅ Saved memory state with heartbeat")
            
            await asyncio.sleep(5)  # 5-second interval
        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")
            await asyncio.sleep(5)

async def main():
    """Main function to run the memory connector"""
    try:
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/memory_connector.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info("Starting memory connector")
        
        # Create memory directory if it doesn't exist
        os.makedirs("memory", exist_ok=True)
        
        # Initialize memory state
        initial_state = load_memory_state()
        save_memory_state(initial_state)
        
        # Start tasks
        bridge_task = asyncio.create_task(connect_to_bridge())
        heartbeat_task_handle = asyncio.create_task(heartbeat_task())
        
        # Wait for tasks to complete (they should run indefinitely)
        await asyncio.gather(bridge_task, heartbeat_task_handle)
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Memory connector stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
EOF
    chmod +x fixed_memory_connector.py
fi

# Update the process sensor for correct bridge port
if [ -f "sensors/enhanced_fixed_process_sensor.py" ]; then
    print_colored "blue" "Updating process sensor bridge URI..."
    # Use sed to update the bridge_uri value
    sed -i.bak 's/bridge_uri="ws:\/\/localhost:8765"/bridge_uri="ws:\/\/localhost:8766"/' sensors/enhanced_fixed_process_sensor.py
    if [ $? -eq 0 ]; then
        print_colored "green" "✅ Updated process sensor bridge URI to port 8766"
    else
        print_colored "yellow" "⚠️ Failed to update process sensor bridge URI"
    fi
fi

# Start services
print_colored "blue" "Starting services..."

# Start the bridge server first
start_service "Bridge Server" "python3 fixed_bridge_connector.py" "logs/bridge/bridge_server.log" "pids/bridge_server.pid"
BRIDGE_SERVER_RESULT=$?

# Wait for bridge server to initialize
sleep 3

# Start the enhanced process sensor
start_service "Enhanced process sensor" "python3 sensors/enhanced_fixed_process_sensor.py" "logs/sensors/process_sensor.log" "pids/process_sensor.pid"
PROCESS_SENSOR_RESULT=$?

# Start the enhanced screen sensor
start_service "Enhanced screen sensor" "python3 sensors/enhanced_fixed_screen_sensor.py" "logs/sensors/screen_sensor.log" "pids/screen_sensor.pid"
SCREEN_SENSOR_RESULT=$?

# Start file sensor
start_service "File sensor" "python3 sensors/file_sensor.py" "logs/sensors/file_sensor.log" "pids/file_sensor.pid"
FILE_SENSOR_RESULT=$?

# Wait for sensors to initialize
sleep 3

# Start enhanced memory connector
start_service "Enhanced memory connector" "python3 fixed_memory_connector.py" "logs/memory/connector.log" "pids/memory_connector.pid"
MEMORY_CONNECTOR_RESULT=$?

# Wait for memory connector to initialize
sleep 2

# Start enhanced WebSocket server
start_service "Enhanced WebSocket server" "python3 enhanced_ws_server.py" "logs/ws_server.log" "pids/ws_server.pid"
WS_SERVER_RESULT=$?

# Start the enhanced backend server using absolute path
start_service "Enhanced backend server" "cd /Users/segevbin/Desktop/SensAI/Aiayer && PYTHONPATH=/Users/segevbin/Desktop/SensAI/Aiayer python3 -m backend.enhanced_backend_server" "logs/backend/backend_server.log" "pids/backend_server.pid"
BACKEND_SERVER_RESULT=$?

# Verify services
print_colored "blue" "Verifying services..."
all_ok=true

# Check each service
if [ $BRIDGE_SERVER_RESULT -ne 0 ]; then
    print_colored "red" "❌ Bridge server failed to start"
    all_ok=false
fi

if [ $PROCESS_SENSOR_RESULT -ne 0 ]; then
    print_colored "red" "❌ Process sensor failed to start"
    all_ok=false
fi

if [ $SCREEN_SENSOR_RESULT -ne 0 ]; then
    print_colored "red" "❌ Screen sensor failed to start"
    all_ok=false
fi

if [ $FILE_SENSOR_RESULT -ne 0 ]; then
    print_colored "red" "❌ File sensor failed to start"
    all_ok=false
fi

if [ $MEMORY_CONNECTOR_RESULT -ne 0 ]; then
    print_colored "red" "❌ Memory connector failed to start"
    all_ok=false
fi

if [ $WS_SERVER_RESULT -ne 0 ]; then
    print_colored "red" "❌ WebSocket server failed to start"
    all_ok=false
fi

if [ $BACKEND_SERVER_RESULT -ne 0 ]; then
    print_colored "red" "❌ Backend server failed to start"
    all_ok=false
fi

# Verify ports are active
if command -v lsof &> /dev/null; then
    # Check Bridge server port
    if lsof -ti :8766 &>/dev/null; then
        print_colored "green" "✅ Bridge server successfully running on port 8766"
    else
        print_colored "red" "❌ Bridge server failed to start on port 8766"
        print_colored "yellow" "See logs/bridge/bridge_server.log for details"
        all_ok=false
    fi
    
    # Check WebSocket server port
    if lsof -ti :8765 &>/dev/null; then
        print_colored "green" "✅ Enhanced WebSocket server successfully running on port 8765"
    else
        print_colored "red" "❌ Enhanced WebSocket server failed to start on port 8765"
        print_colored "yellow" "See logs/ws_server.log for details"
        all_ok=false
    fi
    
    # Check Backend server port
    if lsof -ti :8767 &>/dev/null; then
        print_colored "green" "✅ Enhanced Backend server successfully running on port 8767"
    else
        print_colored "red" "❌ Enhanced Backend server failed to start on port 8767"
        print_colored "yellow" "See logs/backend/backend_server.log for details"
        all_ok=false
    fi
fi

# Final status
if [ "$all_ok" = true ]; then
    print_colored "green" "=========================================================="
    print_colored "green" "✅ Enhanced Context-integrated system is now running!"
    print_colored "green" "=========================================================="
    print_colored "blue" "Bridge server is running on port 8766"
    print_colored "blue" "Enhanced WebSocket server is running on port 8765"
    print_colored "blue" "Enhanced Backend server is running on port 8767"
    print_colored "blue" "Sensors are connected to bridge server on port 8766"
    print_colored "blue" "Memory connector is receiving data from bridge server"
    print_colored "blue" "Memory system is storing context from all sensors"
else
    print_colored "yellow" "System started with some components missing"
    print_colored "yellow" "Check the logs for specific issues"
fi

# Print information about monitoring logs
print_colored "yellow" "To monitor the system:"
echo "tail -f logs/bridge/bridge_server.log     # Bridge server logs"
echo "tail -f logs/ws_server.log                # WebSocket server logs"
echo "tail -f logs/backend/backend_server.log   # Backend server logs"
echo "tail -f logs/sensors/screen_sensor.log    # Screen sensor logs"
echo "tail -f logs/sensors/process_sensor.log   # Process sensor logs"
echo "tail -f logs/memory/connector.log         # Memory connector logs"

print_colored "yellow" "To check context integration, try the following:"
echo "1. View the memory/last_context.json file to see current context"
echo "2. Connect to the Bridge server at ws://127.0.0.1:8766"
echo "3. Connect to the Enhanced WebSocket server at ws://127.0.0.1:8765"
echo "4. Connect to the Enhanced Backend server at ws://127.0.0.1:8767"

# Function to handle shutdown
shutdown() {
    print_colored "yellow" "Shutting down all services..."
    for pid_file in pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            print_colored "blue" "Stopping $name (PID: $pid)..."
            kill -9 $pid 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    # Clean up ports
    kill_port 8765  # Enhanced WebSocket server port
    kill_port 8766  # Bridge server port
    kill_port 8767  # Enhanced Backend server port
    
    print_colored "green" "All services stopped."
    exit 0
}

# Set up trap for graceful shutdown
trap shutdown INT TERM

# Keep the script running
print_colored "blue" "Press Ctrl+C to stop all services"
while true; do
    sleep 1
done