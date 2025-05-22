#!/bin/bash
# run_tauri_with_context.sh
#
# Script to run the Tauri overlay with full context integration
# This starts all necessary backend components and the Tauri dev server

# Set color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored text function
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

# Function to check if port is in use
is_port_in_use() {
    lsof -i:"$1" -P -n | grep LISTEN > /dev/null
    return $?
}

# Function to kill a process using its PID file
kill_process() {
    if [ -f "pids/$1.pid" ]; then
        PID=$(cat "pids/$1.pid")
        if ps -p $PID > /dev/null; then
            print_colored "yellow" "Stopping $1 (PID: $PID)"
            kill $PID
            sleep 1
            if ps -p $PID > /dev/null; then
                print_colored "yellow" "Force stopping $1"
                kill -9 $PID
            fi
        else
            print_colored "yellow" "Process $1 not running with PID $PID"
        fi
        rm "pids/$1.pid"
    else
        print_colored "yellow" "No PID file for $1"
    fi
}

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_colored "red" "Error: npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# First clean up any running components
print_colored "blue" "Cleaning up any existing processes..."
./stop_integrated_memory_system.sh > /dev/null 2>&1

# Create necessary directories
print_colored "blue" "Creating necessary directories..."
mkdir -p logs
mkdir -p pids
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory

# Check required ports
print_colored "blue" "Checking required ports..."
ports_ok=true

if is_port_in_use 8765; then
    print_colored "red" "Port 8765 is already in use. Trying to find the process..."
    lsof -i:8765 -P -n
    ports_ok=false
fi

if is_port_in_use 8766; then
    print_colored "red" "Port 8766 is already in use. Trying to find the process..."
    lsof -i:8766 -P -n
    ports_ok=false
fi

if is_port_in_use 8767; then
    print_colored "red" "Port 8767 is already in use. Trying to find the process..."
    lsof -i:8767 -P -n
    ports_ok=false
fi

if is_port_in_use 1421; then
    print_colored "red" "Port 1421 (Tauri dev server) is already in use. Trying to find the process..."
    lsof -i:1421 -P -n
    ports_ok=false
fi

if [ "$ports_ok" = false ]; then
    print_colored "red" "Some required ports are already in use. Please stop those processes first."
    print_colored "yellow" "You can try running './stop_integrated_memory_system.sh' to clean up."
    exit 1
fi

# Start bridge server
print_colored "blue" "Starting bridge server on port 8766..."
python3 fixed_bridge_server.py > logs/bridge_server.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
sleep 2

# Verify bridge server started
if ! is_port_in_use 8766; then
    print_colored "red" "ERROR: Bridge server failed to start on port 8766"
    cat logs/bridge_server.log
    exit 1
fi

# Start WebSocket server (LLM service)
print_colored "blue" "Starting WebSocket server (LLM service) on port 8765..."
python3 fixed_ws_8765.py > logs/ws_server.log 2>&1 &
WS_PID=$!
echo $WS_PID > pids/ws_server.pid
sleep 2

# Verify WebSocket server started
if ! is_port_in_use 8765; then
    print_colored "red" "ERROR: WebSocket server failed to start on port 8765"
    cat logs/ws_server.log
    exit 1
fi

# Start backend server
print_colored "blue" "Starting backend server on port 8767..."
python3 simple_ws_server_8767.py > logs/backend_server.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > pids/backend_server.pid
sleep 2

# Verify backend server started
if ! is_port_in_use 8767; then
    print_colored "red" "ERROR: Backend server failed to start on port 8767"
    cat logs/backend_server.log
    exit 1
fi

# Start process sensor
print_colored "blue" "Starting process sensor..."
python3 sensors/enhanced_fixed_process_sensor.py > logs/process_sensor.log 2>&1 &
PROCESS_PID=$!
echo $PROCESS_PID > pids/process_sensor.pid
sleep 1

# Start screen sensor
print_colored "blue" "Starting screen sensor..."
python3 sensors/fixed_screen_sensor.py > logs/screen_sensor.log 2>&1 &
SCREEN_PID=$!
echo $SCREEN_PID > pids/screen_sensor.pid
sleep 1

# Start direct sensor to memory connector
print_colored "blue" "Starting direct sensor-to-memory connector..."
python3 direct_sensor_to_memory.py > logs/direct_sensor_memory.log 2>&1 &
DIRECT_PID=$!
echo $DIRECT_PID > pids/direct_sensor_memory.pid
sleep 1

# Start LLM context connector
print_colored "blue" "Starting LLM context connector..."
python3 llm_context_connector.py > logs/llm_context_connector.log 2>&1 &
LLM_CONNECTOR_PID=$!
echo $LLM_CONNECTOR_PID > pids/llm_context_connector.pid
sleep 1

# Verify all components are running
print_colored "blue" "Verifying system components..."
all_running=true

for component in bridge_server ws_server backend_server process_sensor screen_sensor direct_sensor_memory llm_context_connector; do
    if [ -f "pids/$component.pid" ]; then
        pid=$(cat "pids/$component.pid")
        if ps -p $pid > /dev/null; then
            print_colored "green" "✅ $component is running (PID: $pid)"
        else
            print_colored "red" "❌ $component failed to start (PID: $pid)"
            all_running=false
        fi
    else
        print_colored "red" "❌ $component PID file is missing"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    print_colored "red" "Some components failed to start. Check the logs for details."
    print_colored "yellow" "You can still try to continue, but the system may not work correctly."
    print_colored "blue" "Do you want to continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_colored "yellow" "Stopping all components..."
        ./stop_integrated_memory_system.sh > /dev/null 2>&1
        exit 1
    fi
fi

# Wait for memory context to be populated
print_colored "blue" "Waiting for context data to be populated..."
for i in {1..5}; do
    if [ -f "memory/last_context.json" ]; then
        SIZE=$(stat -f%z "memory/last_context.json")
        if [ $SIZE -gt 10 ]; then
            print_colored "green" "✅ Context data is being populated (${SIZE} bytes)"
            break
        fi
    fi
    print_colored "yellow" "Waiting for context data to be populated ($i/5)..."
    sleep 3
done

# Start Tauri dev server
print_colored "blue" "Starting Tauri dev server..."
print_colored "blue" "Changing to overlay directory..."
cd overlay || { 
    print_colored "red" "Failed to change to overlay directory"; 
    print_colored "yellow" "Stopping all components..."; 
    cd ..;
    ./stop_integrated_memory_system.sh > /dev/null 2>&1;
    exit 1; 
}

# Check npm dependencies
if [ ! -d "node_modules" ]; then
    print_colored "yellow" "Node modules not found. Installing dependencies..."
    npm install || {
        print_colored "red" "Failed to install npm dependencies";
        print_colored "yellow" "Stopping all components...";
        cd ..;
        ./stop_integrated_memory_system.sh > /dev/null 2>&1;
        exit 1;
    }
fi

# Run Tauri dev server
print_colored "green" "==================================================="
print_colored "green" "Starting Tauri dev server with context integration"
print_colored "green" "==================================================="
print_colored "blue" "The system is now running with:"
print_colored "blue" "- WebSocket server on port 8765 (LLM service)"
print_colored "blue" "- Bridge server on port 8766"
print_colored "blue" "- Backend server on port 8767"
print_colored "blue" "- Process and screen sensors"
print_colored "blue" "- LLM context connector"
print_colored "blue" "- Tauri dev server on port 1421"
print_colored "yellow" "To stop everything when done, press Ctrl+C and then run:"
print_colored "yellow" "./stop_integrated_memory_system.sh"

# Run Tauri dev with proper error handling
if ! npm run tauri dev; then
    print_colored "red" "Tauri dev server exited with an error"
else
    print_colored "green" "Tauri dev server exited successfully"
fi

# Go back to original directory
cd ..

# Ask if user wants to stop all components
print_colored "blue" "Do you want to stop all backend components? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    print_colored "yellow" "Stopping all components..."
    ./stop_integrated_memory_system.sh
else
    print_colored "yellow" "Backend components are still running."
    print_colored "yellow" "You can stop them later with: ./stop_integrated_memory_system.sh"
fi

print_colored "blue" "Script finished."