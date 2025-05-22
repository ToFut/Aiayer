#!/bin/bash
# fixed_start_optimized_system_v3.sh
# A comprehensive fix that properly handles connect_sensor_to_memory

set -e
echo "=== Starting Fixed Optimized Aiayer System v3 ==="

# Create required directories
echo "Creating required directories..."
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p logs/sensors/sensor_screen
mkdir -p pids
mkdir -p data

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
  echo "{
    \"version\": \"1.0\",
    \"last_update\": \"$(date -u +"%Y-%m-%dT%H:%M:%S.%NZ")\",
    \"context\": {},
    \"short_term\": [],
    \"long_term\": []
  }" > "memory/memory_state.json"
fi

if [ ! -f "memory/last_context.json" ] || [ ! -s "memory/last_context.json" ]; then
  echo "{
    \"timestamp\": $(date +%s),
    \"active_window\": \"\",
    \"active_app\": \"\",
    \"active_apps\": [],
    \"window_history\": [],
    \"screen_text\": \"\"
  }" > "memory/last_context.json"
fi

# Function to kill processes
kill_process() {
  process_name=$1
  echo "Stopping ${process_name} processes..."
  pids=$(ps aux | grep -i "${process_name}" | grep -v grep | awk '{print $2}')
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
kill_process "memory_connector"
kill_process "fixed_ws_server"
kill_process "fixed_memory_connector"
kill_process "websocket"
kill_process "simple_ws_server_8767"

# Check for processes using port 8767
echo "Checking for processes using port 8767..."
if command -v lsof &> /dev/null; then
  pid=$(lsof -ti :8767 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "Killing process $pid using port 8767"
    kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
    sleep 1
  fi
fi

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

# Initialize last_screen.json
echo '{
  "timestamp": '$(date +%s)',
  "screen_text": "",
  "has_images": false,
  "has_videos": false
}' > "cache/screen_sensor/last_screen.json"

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

# Create memory connector script
echo "Creating memory connector script..."
cat > fixed_memory_connector.py << EOF
#!/usr/bin/env python3
"""
Fixed Memory Connector

This script connects the sensors to memory, ensuring that sensor data
is properly stored and processed.
"""
import json
import os
import time
import logging
import sys
from datetime import datetime

# Setup directories
os.makedirs('logs/memory', exist_ok=True)
os.makedirs('memory', exist_ok=True)
os.makedirs('pids', exist_ok=True)

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

def save_pid():
    """Save PID to file"""
    try:
        with open('pids/memory_connector.pid', 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"Error saving PID: {e}")
        return False

def load_process_cache():
    """Load process sensor cache"""
    try:
        with open('cache/process_sensor/process_cache.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Process cache file issue: {e}")
        return {"timestamp": int(time.time()), "active_window": "", "active_app": "", "active_apps": [], "window_history": []}

def load_screen_cache():
    """Load screen sensor cache"""
    try:
        with open('cache/screen_sensor/screen_cache.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Screen cache file issue: {e}")
        return {"timestamp": int(time.time()), "screen_text": "", "has_images": False, "has_videos": False}

def update_context():
    """Update context with latest sensor data"""
    try:
        # Load sensor data
        process_data = load_process_cache()
        screen_data = load_screen_cache()
        
        # Create combined context
        context = {
            "timestamp": int(time.time()),
            "active_window": process_data.get("active_window", ""),
            "active_app": process_data.get("active_app", ""),
            "active_apps": process_data.get("active_apps", []),
            "window_history": process_data.get("window_history", []),
            "screen_text": screen_data.get("screen_text", "")
        }
        
        # Save context
        with open('memory/last_context.json', 'w') as f:
            json.dump(context, f, indent=2)
        
        return context
    except Exception as e:
        logger.error(f"Error updating context: {e}")
        return None

def run_memory_connector():
    """Main memory connector loop"""
    logger.info("Starting fixed memory connector")
    
    # Save PID
    if not save_pid():
        logger.error("Failed to save PID, exiting")
        sys.exit(1)
    
    # Initial memory state
    try:
        memory_state = load_memory_state()
    except Exception as e:
        logger.error(f"Failed to initialize memory state: {e}")
        sys.exit(1)
    
    # Monitor loop
    try:
        while True:
            # Update context from sensors
            context = update_context()
            if context:
                # Update memory state with context
                memory_state["last_update"] = datetime.now().isoformat()
                memory_state["context"] = context
                
                # Save updated state
                if save_memory_state(memory_state):
                    logger.debug("Memory state updated with latest context")
            
            # Sleep to avoid high CPU usage
            time.sleep(2)
            
    except KeyboardInterrupt:
        logger.info("Memory connector stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in memory connector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_memory_connector()
EOF

# Make the memory connector executable
chmod +x fixed_memory_connector.py

# Start backend services
echo "Starting backend services..."

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

# Wait for sensors to initialize
sleep 2

# Start memory connector
echo "Starting memory connector..."
python3 fixed_memory_connector.py > logs/memory/connector.log 2>&1 &
CONNECTOR_PID=$!
echo $CONNECTOR_PID > pids/memory_connector.pid
echo "Memory connector started with PID $CONNECTOR_PID"

# Wait for memory connector to initialize
sleep 2

# Create WebSocket server script
echo "Creating WebSocket server script..."
cat > fixed_ws_server.py << EOF
#!/usr/bin/env python3
"""
Fixed WebSocket Server with Memory Integration

Enhanced WebSocket server that connects to the memory system.
"""
import asyncio
import json
import logging
import websockets
import sys
import os
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

# Memory state path
MEMORY_STATE_PATH = "memory/memory_state.json"
LAST_CONTEXT_PATH = "memory/last_context.json"

def load_memory_state():
    """Load memory state from file"""
    try:
        with open(MEMORY_STATE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading memory state: {e}")
        return {"last_update": datetime.now().isoformat()}

def load_context():
    """Load last context from file"""
    try:
        with open(LAST_CONTEXT_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading context: {e}")
        return {"timestamp": int(time.time())}

async def handler(websocket):
    """Handle WebSocket connections with memory integration."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message with memory state
        memory_state = load_memory_state()
        context = load_context()
        
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": f"Connected to WebSocket server with memory integration",
                "memory_last_update": memory_state.get("last_update", "unknown"),
                "context_timestamp": context.get("timestamp", 0),
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Process based on message type
                if data.get("type") == "get_memory":
                    # Return current memory state
                    memory_state = load_memory_state()
                    await websocket.send(json.dumps({
                        "type": "memory_state",
                        "data": memory_state,
                        "timestamp": datetime.now().isoformat()
                    }))
                elif data.get("type") == "get_context":
                    # Return current context
                    context = load_context()
                    await websocket.send(json.dumps({
                        "type": "context_data",
                        "data": context,
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
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
        if client_id:  # Only try to remove if client_id is defined
            try:
                connected_clients.remove(websocket)
            except KeyError:
                pass  # Client may have already been removed

async def broadcast_updates():
    """Periodically broadcast memory updates to all clients."""
    last_update = ""
    
    while True:
        if connected_clients:
            try:
                # Check for memory state updates
                memory_state = load_memory_state()
                current_update = memory_state.get("last_update", "")
                
                if current_update != last_update:
                    last_update = current_update
                    
                    message = json.dumps({
                        "type": "memory_update",
                        "data": {
                            "last_update": current_update,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    
                    # Broadcast to all clients
                    await asyncio.gather(
                        *[client.send(message) for client in connected_clients],
                        return_exceptions=True
                    )
            except Exception as e:
                logger.error(f"Error in broadcast: {e}")
        
        await asyncio.sleep(2)

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Save PID
        with open("pids/fixed_ws_server.pid", "w") as f:
            f.write(str(os.getpid()))
        
        # Create the server with new API style
        async with websockets.serve(
            handler,
            "127.0.0.1",
            8767,
            ping_interval=10,
            ping_timeout=5,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            max_queue=64                # Queue size
        ):
            logger.info("Fixed WebSocket server started on ws://127.0.0.1:8767 with memory integration")
            
            # Start broadcast task
            broadcast_task = asyncio.create_task(broadcast_updates())
            
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

# Make the WebSocket server executable
chmod +x fixed_ws_server.py

# Check if websockets module is installed
echo "Checking for websockets module..."
if ! python3 -c "import websockets" 2>/dev/null; then
  echo "❌ websockets module not found, attempting to install..."
  pip3 install websockets || {
    echo "❌ Failed to install websockets module"
    echo "Please install manually with: pip3 install websockets"
    exit 1
  }
  echo "✅ websockets module installed"
fi

# Start WebSocket server
echo "Starting WebSocket server..."
python3 fixed_ws_server.py > logs/fixed_ws_server.log 2>&1 &
WS_SERVER_PID=$!
echo $WS_SERVER_PID > pids/fixed_ws_server.pid
echo "WebSocket server started with PID $WS_SERVER_PID"

# Wait for server to initialize
sleep 2

# Verify services are running
echo "Verifying services..."
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        service_name=$(basename "$pid_file" .pid)
        if ps -p $pid > /dev/null; then
            echo "✅ Service $service_name is running (PID: $pid)"
        else
            echo "❌ Service $service_name failed to start"
            echo "Check logs for details"
        fi
    fi
done

# Verify WebSocket server
if command -v lsof &> /dev/null; then
    if lsof -ti :8767 &>/dev/null; then
        echo "✅ WebSocket server successfully running on port 8767"
    else
        echo "❌ WebSocket server failed to start on port 8767"
        echo "See logs/fixed_ws_server.log for details"
        cat logs/fixed_ws_server.log
    fi
fi

echo "=== System Started Successfully ==="
echo "The system is now running with memory integration"
echo "Process sensor PID: $PROCESS_SENSOR_PID"
echo "Screen sensor PID: $SCREEN_SENSOR_PID"
echo "File sensor PID: $FILE_SENSOR_PID"
echo "Memory connector PID: $CONNECTOR_PID"
echo "WebSocket server PID: $WS_SERVER_PID (running on port 8767)"
echo ""
echo "IMPORTANT: The WebSocket server is running on port 8767"
echo "Connect to: ws://127.0.0.1:8767"
echo ""
echo "To check logs, use:"
echo "tail -f logs/fixed_ws_server.log   # WebSocket server logs"
echo "tail -f logs/memory/connector.log  # Memory connector logs"
echo "tail -f logs/sensors/process_sensor.log  # Process sensor logs"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid 2>/dev/null)"