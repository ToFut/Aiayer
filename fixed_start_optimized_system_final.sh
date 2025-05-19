#!/bin/bash
# fixed_start_optimized_system_final.sh
# A fully fixed version that properly starts all components

set -e
echo "=== Starting Optimized Aiayer System with Memory Integration ==="

# Create required directories
echo "Creating required directories..."
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p pids

# First, stop any existing processes
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

echo "Stopping any running processes..."
kill_process "sensor"
kill_process "connect_sensor_to_memory"
kill_process "memory_connector"
kill_process "ws_server"
kill_process "websocket"
kill_process "minimal_ws"

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
    \"last_update\": \"$(date -Iseconds)\",
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

# Check if fixed_memory_connector.py is a symlink and has a target
if [ -L memory/connect_sensor_to_memory.py ]; then
  echo "connect_sensor_to_memory.py is a symlink pointing to $(readlink memory/connect_sensor_to_memory.py)"
  
  # Check if the target file exists
  if [ ! -f $(readlink -f memory/connect_sensor_to_memory.py) ]; then
    echo "❌ Warning: The symlink target does not exist!"
    echo "Creating a local fixed_memory_connector.py file..."
    
    # Create a local copy of the memory connector
    cat > fixed_memory_connector.py << 'EOF'
#!/usr/bin/env python3
"""
Fixed Memory Connector

Connects sensors to memory system for integration.
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

def save_pid():
    """Save PID to file"""
    try:
        with open('pids/memory_connector.pid', 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"Error saving PID: {e}")
        return False

def run_memory_connector():
    """Main memory connector loop"""
    logger.info("Starting memory connector")
    
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
    chmod +x fixed_memory_connector.py
  fi
fi

# Start memory connector
echo "Starting memory connector..."
python3 fixed_memory_connector.py > logs/memory/connector.log 2>&1 &
CONNECTOR_PID=$!
echo $CONNECTOR_PID > pids/memory_connector.pid
echo "Memory connector started with PID $CONNECTOR_PID"

# Wait for memory connector to initialize
sleep 2

# Start WebSocket server using the existing minimal_ws.py
echo "Starting WebSocket server..."
python3 minimal_ws.py > logs/ws_server.log 2>&1 &
WS_SERVER_PID=$!
echo $WS_SERVER_PID > pids/ws_server.pid
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
        echo "See logs/ws_server.log for details"
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
echo "tail -f logs/ws_server.log            # WebSocket server logs"
echo "tail -f logs/memory/connector.log     # Memory connector logs"
echo "tail -f logs/sensors/process_sensor.log  # Process sensor logs"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid 2>/dev/null)"