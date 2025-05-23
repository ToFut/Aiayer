#!/bin/bash
# run_integrated_memory_system.sh - Comprehensive system to ensure sensor data populates memory

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored text
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

# Create directories
print_colored "blue" "Creating directories..."
mkdir -p logs/sensors/screen_sensor
mkdir -p logs/sensors/process_sensor
mkdir -p logs/memory
mkdir -p logs/bridge
mkdir -p logs/monitoring
mkdir -p logs/llm
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p cache/file_sensor
mkdir -p memory

# Kill process using a port
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

# Kill processes by name
kill_process() {
    process_name=$1
    pids=$(ps aux | grep -i "${process_name}" | grep -v grep | awk '{print $2}')
    if [ -n "$pids" ]; then
        print_colored "yellow" "Killing processes: $pids"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || true
        done
    fi
}

# Clean up any existing processes
print_colored "yellow" "Cleaning up existing processes..."
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        name=$(basename "$pid_file" .pid)
        print_colored "yellow" "Stopping previous $name (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        rm -f "$pid_file"
    fi
done

# Kill processes by name
kill_process "python3 direct_sensor_to_memory.py"
kill_process "python3 sensors/enhanced_fixed_process_sensor.py"
kill_process "python3 sensors/total_screen_analyzer.py"
kill_process "python3 fixed_bridge_server_enhanced.py"
kill_process "python3 fixed_ws_8765.py"
kill_process "python3 simple_ws_server_8767.py"
kill_process "python3 monitor_context_integration.py"
kill_process "python3 llm_context_connector.py"

# Clean up ports
print_colored "yellow" "Cleaning up ports..."
kill_port 8765  # WebSocket server port
kill_port 8766  # Bridge server port
kill_port 8767  # Backend server port
kill_port 8768  # Enhanced bridge port
kill_port 8769  # Memory server port
sleep 2

# Fix port in bridge server script
print_colored "blue" "Fixing port configuration in bridge server..."
sed -i.bak 's/WS_PORT = 8768/WS_PORT = 8766/' fixed_bridge_server_enhanced.py
sed -i.bak 's/MEMORY_SERVER_PORT = 8769/MEMORY_SERVER_PORT = 8767/' fixed_bridge_server_enhanced.py

# Fix port in sensors
print_colored "blue" "Fixing port configuration in sensors..."
sed -i.bak 's/bridge_uri="ws:\/\/localhost:8765"/bridge_uri="ws:\/\/localhost:8766"/' sensors/enhanced_fixed_process_sensor.py
sed -i.bak 's/bridge_uri="ws:\/\/localhost:8765"/bridge_uri="ws:\/\/localhost:8766"/' sensors/total_screen_analyzer.py

# Initialize files
print_colored "blue" "Initializing essential files..."
timestamp=$(date +%s)

# Initialize context file
echo '{
    "timestamp": '${timestamp}',
    "active_window": "",
    "active_app": "",
    "active_apps": [],
    "window_history": [],
    "screen_text": ""
}' > "memory/last_context.json"

# Initialize memory state
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

# Initialize process cache
echo '{
    "timestamp": '${timestamp}',
    "active_window": "",
    "active_app": "",
    "active_apps": [],
    "window_history": []
}' > "cache/process_sensor/process_cache.json"

# Initialize screen cache
echo '{
    "timestamp": '${timestamp}',
    "screen_text": "",
    "has_images": false,
    "has_videos": false
}' > "cache/screen_sensor/last_screen.json"

print_colored "green" "Files prepared"

# Start a service and capture its PID
start_service() {
    service_name=$1
    command=$2
    log_file=$3
    pid_file=$4
    
    print_colored "blue" "Starting $service_name..."
    mkdir -p $(dirname "$log_file")
    
    eval "$command > $log_file 2>&1 &"
    pid=$!
    echo $pid > $pid_file
    
    # Wait for process to start
    sleep 2
    if ps -p $pid > /dev/null; then
        print_colored "green" "✅ $service_name started with PID: $pid"
        return 0
    else
        print_colored "red" "❌ $service_name failed to start"
        return 1
    fi
}

# Start services
print_colored "blue" "Starting services..."

# 1. Start bridge server
start_service "Bridge Server" "python3 fixed_bridge_server_enhanced.py" "logs/bridge/bridge_server.log" "pids/bridge_server.pid"
BRIDGE_RESULT=$?

# Wait for bridge server to initialize
sleep 3

# 2. Start WebSocket server
start_service "WebSocket Server" "python3 fixed_ws_8765.py" "logs/ws_server.log" "pids/ws_server.pid"
WS_RESULT=$?

# 3. Start backend server
start_service "Backend Server" "python3 simple_ws_server_8767.py" "logs/backend_server.log" "pids/backend_server.pid"
BACKEND_RESULT=$?

# Wait for servers to initialize
sleep 3

# 4. Start sensors
start_service "Process Sensor" "python3 sensors/enhanced_fixed_process_sensor.py" "logs/sensors/process_sensor.log" "pids/process_sensor.pid"
PROCESS_RESULT=$?

start_service "Total Screen Analyzer" "python3 sensors/total_screen_analyzer.py" "logs/sensors/total_screen_analyzer.log" "pids/total_screen_analyzer.pid"
SCREEN_RESULT=$?

# Wait for sensors to initialize
sleep 2

# 5. Start direct sensor to memory integration
start_service "Direct Sensor-Memory Integration" "python3 direct_sensor_to_memory.py" "logs/memory/direct_integration.log" "pids/direct_sensor_memory.pid"
DIRECT_RESULT=$?

# 6. Start LLM context connector
start_service "LLM Context Connector" "python3 llm_context_connector.py" "logs/llm/llm_context.log" "pids/llm_context.pid"
LLM_RESULT=$?

# 7. Start monitor
start_service "Context Integration Monitor" "python3 monitor_context_integration.py" "logs/monitoring/context_monitor.log" "pids/context_monitor.pid"
MONITOR_RESULT=$?

# Verify services
print_colored "blue" "Verifying services..."
all_ok=true

# Check each service
if [ $BRIDGE_RESULT -ne 0 ]; then
    print_colored "red" "❌ Bridge server failed to start"
    all_ok=false
fi

if [ $WS_RESULT -ne 0 ]; then
    print_colored "red" "❌ WebSocket server failed to start"
    all_ok=false
fi

if [ $BACKEND_RESULT -ne 0 ]; then
    print_colored "red" "❌ Backend server failed to start"
    all_ok=false
fi

if [ $PROCESS_RESULT -ne 0 ]; then
    print_colored "red" "❌ Process sensor failed to start"
    all_ok=false
fi

if [ $SCREEN_RESULT -ne 0 ]; then
    print_colored "red" "❌ Screen sensor failed to start"
    all_ok=false
fi

if [ $DIRECT_RESULT -ne 0 ]; then
    print_colored "red" "❌ Direct sensor-memory integration failed to start"
    all_ok=false
fi

if [ $LLM_RESULT -ne 0 ]; then
    print_colored "red" "❌ LLM context connector failed to start"
    all_ok=false
fi

if [ $MONITOR_RESULT -ne 0 ]; then
    print_colored "red" "❌ Context integration monitor failed to start"
    all_ok=false
fi

# Verify ports
print_colored "blue" "Verifying port bindings..."

# Check Bridge server port
if command -v lsof &> /dev/null && lsof -ti :8766 &>/dev/null; then
    print_colored "green" "✅ Bridge server is running on port 8766"
else
    print_colored "red" "❌ Bridge server is not running on port 8766"
    all_ok=false
fi

# Check WebSocket server port
if command -v lsof &> /dev/null && lsof -ti :8765 &>/dev/null; then
    print_colored "green" "✅ WebSocket server is running on port 8765"
else
    print_colored "red" "❌ WebSocket server is not running on port 8765"
    all_ok=false
fi

# Check Backend server port
if command -v lsof &> /dev/null && lsof -ti :8767 &>/dev/null; then
    print_colored "green" "✅ Backend server is running on port 8767"
else
    print_colored "red" "❌ Backend server is not running on port 8767"
    all_ok=false
fi

# Final status
if [ "$all_ok" = true ]; then
    print_colored "green" "=================================================="
    print_colored "green" "✅ Integrated memory system is now running!"
    print_colored "green" "=================================================="
else
    print_colored "yellow" "System started with some components missing"
    print_colored "yellow" "Check the logs for specific issues"
fi

# Wait for system to start collecting data
print_colored "blue" "Waiting 15 seconds for data collection..."
sleep 15

# Verify memory is being populated
print_colored "blue" "Verifying memory population..."

# Check memory state file size
if [ -f "memory/memory_state.json" ]; then
    size=$(wc -c < "memory/memory_state.json")
    if [ $size -gt 200 ]; then
        print_colored "green" "✅ Memory state file has data ($size bytes)"
    else
        print_colored "red" "❌ Memory state file may be empty ($size bytes)"
    fi
else
    print_colored "red" "❌ Memory state file does not exist"
fi

# Check context file
if [ -f "memory/last_context.json" ]; then
    size=$(wc -c < "memory/last_context.json")
    if [ $size -gt 200 ]; then
        print_colored "green" "✅ Context file has data ($size bytes)"
        
        # Show context info
        print_colored "blue" "Context information:"
        cat "memory/last_context.json" | grep -E "active_window|active_app|timestamp" | sed 's/^/    /'
    else
        print_colored "red" "❌ Context file may be empty ($size bytes)"
    fi
else
    print_colored "red" "❌ Context file does not exist"
fi

# Verify LLM context connector is sending updates
print_colored "blue" "Verifying LLM context integration..."
if [ -f "logs/llm/llm_context.log" ]; then
    if grep -q "Sent periodic context update" "logs/llm/llm_context.log"; then
        print_colored "green" "✅ LLM context connector is sending updates"
        # Show last context update time
        last_update=$(grep "Sent periodic context update" "logs/llm/llm_context.log" | tail -1 | sed 's/.*\[\(.*\)\].*/\1/')
        print_colored "blue" "Last context update: $last_update"
    else
        print_colored "red" "❌ No LLM context updates found in logs"
    fi
else
    print_colored "red" "❌ LLM context log file does not exist"
fi

# Information about monitoring
print_colored "yellow" "To monitor the system:"
echo "tail -f logs/memory/direct_integration.log      # Direct integration logs"
echo "tail -f logs/bridge/bridge_server.log           # Bridge server logs"
echo "tail -f logs/monitoring/context_monitor.log     # Context monitor logs"
echo "tail -f logs/sensors/process_sensor.log         # Process sensor logs"
echo "tail -f logs/sensors/screen_sensor.log          # Screen sensor logs"
echo "tail -f logs/llm/llm_context.log                # LLM context connector logs"
echo "tail -f logs/ws_server.log                      # WebSocket server logs"

# Keep the script running
print_colored "blue" "Press Ctrl+C to stop all services"
trap 'print_colored "yellow" "Stopping all services..."; for pid_file in pids/*.pid; do if [ -f "$pid_file" ]; then pid=$(cat "$pid_file"); kill -9 $pid 2>/dev/null || true; rm -f "$pid_file"; fi; done; exit 0' INT
while true; do
    sleep 1
done