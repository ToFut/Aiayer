#!/bin/bash
# fixed_context_integration_system.sh
# Complete solution for context integration with direct sensor-to-memory connection

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
kill_process "direct_sensor_to_memory.py"

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
        "context": {
            "active_window": "",
            "active_app": "",
            "active_apps": [],
            "window_history": [],
            "screen_text": ""
        },
        "short_term": [],
        "long_term": [],
        "sensor_data": {
            "screen": {},
            "process": {},
            "file": {}
        }
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

# Start services in the correct order
print_colored "blue" "Starting services..."

# 1. Start the enhanced bridge server
start_service "Enhanced Bridge Server" "python3 fixed_bridge_server_enhanced.py" "logs/bridge/bridge_server.log" "pids/bridge_server.pid"
BRIDGE_SERVER_RESULT=$?

# Wait for bridge server to initialize
sleep 3

# 2. Start sensors
start_service "Process sensor" "python3 sensors/enhanced_fixed_process_sensor.py" "logs/sensors/process_sensor.log" "pids/process_sensor.pid"
PROCESS_SENSOR_RESULT=$?

start_service "Screen sensor" "python3 sensors/enhanced_fixed_screen_sensor.py" "logs/sensors/screen_sensor.log" "pids/screen_sensor.pid" 
SCREEN_SENSOR_RESULT=$?

# Wait for sensors to initialize
sleep 3

# 3. Start direct sensor to memory integration (our new solution)
start_service "Direct Sensor-Memory Integration" "python3 direct_sensor_to_memory.py" "logs/memory/direct_integration.log" "pids/direct_sensor_memory.pid"
DIRECT_INTEGRATION_RESULT=$?

# Wait for direct integration to initialize
sleep 2

# 4. Start WebSocket server
start_service "WebSocket Server" "python3 fixed_ws_8765.py" "logs/ws_server.log" "pids/ws_server.pid"
WS_SERVER_RESULT=$?

# 5. Start backend server
start_service "Backend Server" "python3 simple_ws_server_8767.py" "logs/backend_server.log" "pids/backend_server.pid"
BACKEND_SERVER_RESULT=$?

# 6. Start context integration monitor
start_service "Context Integration Monitor" "python3 monitor_context_integration.py" "logs/monitoring/context_monitor.log" "pids/context_monitor.pid"
MONITOR_RESULT=$?

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

if [ $DIRECT_INTEGRATION_RESULT -ne 0 ]; then
    print_colored "red" "❌ Direct sensor-memory integration failed to start"
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

if [ $MONITOR_RESULT -ne 0 ]; then
    print_colored "red" "❌ Context integration monitor failed to start"
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
        print_colored "green" "✅ WebSocket server successfully running on port 8765"
    else
        print_colored "red" "❌ WebSocket server failed to start on port 8765"
        print_colored "yellow" "See logs/ws_server.log for details"
        all_ok=false
    fi
    
    # Check Backend server port
    if lsof -ti :8767 &>/dev/null; then
        print_colored "green" "✅ Backend server successfully running on port 8767"
    else
        print_colored "red" "❌ Backend server failed to start on port 8767"
        print_colored "yellow" "See logs/backend_server.log for details"
        all_ok=false
    fi
fi

# Final status
if [ "$all_ok" = true ]; then
    print_colored "green" "=========================================================="
    print_colored "green" "✅ Enhanced Context-integrated system is now running!"
    print_colored "green" "=========================================================="
    print_colored "blue" "Bridge server is running on port 8766"
    print_colored "blue" "WebSocket server is running on port 8765"
    print_colored "blue" "Backend server is running on port 8767"
    print_colored "blue" "Sensors are connected to bridge server on port 8766"
    print_colored "blue" "Direct sensor-to-memory integration is active"
    print_colored "blue" "Memory state is being continuously updated"
    print_colored "blue" "Context integration monitor is actively verifying data flow"
else
    print_colored "yellow" "System started with some components missing"
    print_colored "yellow" "Check the logs for specific issues"
fi

# Verification check of memory system
print_colored "blue" "Performing memory system verification..."
sleep 10 # Allow some time for data to be collected

# Check if memory state has been updated
if [ -f "memory/memory_state.json" ]; then
    STATE_SIZE=$(wc -c < "memory/memory_state.json")
    if [ $STATE_SIZE -gt 200 ]; then
        print_colored "green" "✅ Memory state file exists and has data"
    else
        print_colored "yellow" "⚠️ Memory state file exists but may be empty"
    fi
else
    print_colored "red" "❌ Memory state file does not exist"
fi

# Check if last_context.json has been updated
if [ -f "memory/last_context.json" ]; then
    CONTEXT_SIZE=$(wc -c < "memory/last_context.json")
    if [ $CONTEXT_SIZE -gt 200 ]; then
        print_colored "green" "✅ Context file exists and has data"
        
        # Display some context info
        print_colored "blue" "Context information:"
        cat "memory/last_context.json" | grep -E "active_window|active_app|timestamp" | sed 's/^/    /'
    else
        print_colored "yellow" "⚠️ Context file exists but may be empty"
    fi
else
    print_colored "red" "❌ Context file does not exist"
fi

# Print information about monitoring logs
print_colored "yellow" "To monitor the system:"
echo "tail -f logs/direct_integration.log            # Direct integration logs"
echo "tail -f logs/bridge/bridge_server.log          # Bridge server logs"
echo "tail -f logs/ws_server.log                     # WebSocket server logs"
echo "tail -f logs/backend_server.log                # Backend server logs"
echo "tail -f logs/sensors/screen_sensor.log         # Screen sensor logs"
echo "tail -f logs/sensors/process_sensor.log        # Process sensor logs"
echo "tail -f logs/monitoring/context_monitor.log    # Context integration monitor logs"

print_colored "yellow" "To check context integration:"
echo "1. View memory/last_context.json - This file should contain current active applications and windows"
echo "2. View memory/memory_state.json - This file should contain comprehensive memory state with sensor data"
echo "3. Check if data is flowing properly:"
echo "   cat cache/process_sensor/process_cache.json | grep active_app"
echo "   cat memory/last_context.json | grep active_app"

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
    kill_port 8765  # WebSocket server port
    kill_port 8766  # Bridge server port
    kill_port 8767  # Backend server port
    
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