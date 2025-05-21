#!/bin/bash
# start_context_integrated_system.sh
# Updated script to properly start the whole system with working components

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

# Clean up ports
print_colored "yellow" "Cleaning up ports..."
kill_port 8765  # Enhanced WebSocket server port
kill_port 8767  # Enhanced Backend server port
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

# Create memory connector if needed
if [ ! -f "fixed_memory_connector.py" ]; then
    print_colored "blue" "Creating memory connector script..."
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

# Start services
print_colored "blue" "Starting services..."

# Start the enhanced process sensor
start_service "enhanced process sensor" "python3 sensors/enhanced_fixed_process_sensor.py" "logs/sensors/process_sensor.log" "pids/process_sensor.pid"
PROCESS_SENSOR_RESULT=$?

# Start the enhanced screen sensor
start_service "enhanced screen sensor" "python3 sensors/enhanced_fixed_screen_sensor.py" "logs/sensors/screen_sensor.log" "pids/screen_sensor.pid"
SCREEN_SENSOR_RESULT=$?

# Start file sensor
start_service "file sensor" "python3 sensors/file_sensor.py" "logs/sensors/file_sensor.log" "pids/file_sensor.pid"
FILE_SENSOR_RESULT=$?

# Wait for sensors to initialize
sleep 2

# Start enhanced memory connector
start_service "enhanced memory connector" "python3 memory/enhanced_memory_connector.py" "logs/memory/connector.log" "pids/memory_connector.pid"
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

# Verify WebSocket server and backend server ports
if command -v lsof &> /dev/null; then
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
    print_colored "blue" "Enhanced WebSocket server is running on port 8765"
    print_colored "blue" "Enhanced Backend server is running on port 8767"
    print_colored "blue" "Enhanced Backend server is providing integrated functionality"
    print_colored "blue" "Enhanced Memory system is providing context from sensors"
    print_colored "blue" "Enhanced Screen and Process sensors are capturing context"
else
    print_colored "yellow" "System started with some components missing"
    print_colored "yellow" "Check the logs for specific issues"
fi

# Print information about monitoring logs
print_colored "yellow" "To monitor the system:"
echo "tail -f logs/ws_server.log                 # WebSocket server logs"
echo "tail -f logs/backend/backend_server.log    # Backend server logs"
echo "tail -f logs/sensors/screen_sensor.log     # Screen sensor logs"
echo "tail -f logs/sensors/process_sensor.log    # Process sensor logs"
echo "tail -f logs/memory/connector.log          # Memory connector logs"

print_colored "yellow" "To check context integration, try the following:"
echo "1. View the memory/last_context.json file to see current context"
echo "2. Connect to the Enhanced WebSocket server at ws://127.0.0.1:8765"
echo "3. Connect to the Enhanced Backend server at ws://127.0.0.1:8767"

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