#!/bin/bash
# Core system startup script with only essential components
# Focuses on the core memory system, sensors, and LLM integration

# Function to print colored output
print_colored() {
    COLOR=$1
    TEXT=$2
    
    case $COLOR in
        "red") echo -e "\033[0;31m$TEXT\033[0m" ;;
        "green") echo -e "\033[0;32m$TEXT\033[0m" ;;
        "yellow") echo -e "\033[0;33m$TEXT\033[0m" ;;
        "blue") echo -e "\033[0;34m$TEXT\033[0m" ;;
        *) echo "$TEXT" ;;
    esac
}

# Function to check if directory exists and create if it doesn't
ensure_dir() {
    if [ ! -d "$1" ]; then
        print_colored "yellow" "Creating directory: $1"
        mkdir -p "$1"
    fi
}

# Function to start a service and verify it's running
start_service() {
    SERVICE_NAME=$1
    COMMAND=$2
    LOG_FILE=$3
    PID_FILE=$4
    
    print_colored "yellow" "Starting ${SERVICE_NAME}..."
    $COMMAND > $LOG_FILE 2>&1 &
    SERVICE_PID=$!
    sleep 1
    
    # Check if process is still running
    if ps -p $SERVICE_PID > /dev/null; then
        echo $SERVICE_PID > $PID_FILE
        print_colored "green" "✅ ${SERVICE_NAME} started with PID $SERVICE_PID"
        return 0
    else
        print_colored "red" "❌ ${SERVICE_NAME} failed to start"
        # Print the error log for debugging
        echo "Error log:"
        tail -n 10 $LOG_FILE
        return 1
    fi
}

# Check if Ollama is installed and running
if ! command -v ollama &> /dev/null; then
    print_colored "red" "❌ Ollama is not installed. Please install it first:"
    print_colored "yellow" "   Visit https://ollama.ai/download for installation instructions"
    exit 1
fi

# Check if Ollama service is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    print_colored "yellow" "Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    ensure_dir "pids"
    echo $OLLAMA_PID > pids/ollama.pid
    sleep 5  # Give Ollama time to start
fi

# Create necessary directories
print_colored "blue" "Creating necessary directories..."
ensure_dir "logs/sensors/screen_sensor"
ensure_dir "logs/sensors/process_sensor"
ensure_dir "logs/sensors/file_sensor"
ensure_dir "logs/llm"
ensure_dir "logs/memory"
ensure_dir "logs/backend"
ensure_dir "pids"
ensure_dir "cache/screen_sensor"
ensure_dir "cache/process_sensor"
ensure_dir "cache/file_sensor"
ensure_dir "memory"

# Initialize memory system files
print_colored "blue" "Initializing memory system files..."
touch memory/short_term.idx memory/long_term.idx
echo "[]" > memory/short_term_metadata.json
echo "{}" > memory/conversation_history.json
echo "{}" > memory/memory_state.json
echo "{
  \"timestamp\": $(date +%s),
  \"active_window\": \"\",
  \"active_app\": \"\",
  \"active_apps\": [],
  \"window_history\": [],
  \"screen_text\": \"\"
}" > memory/last_context.json

# Use minimal logging configuration
print_colored "blue" "Setting up minimal logging configuration..."
cp config/logging.conf.minimal config/logging.conf

# Kill any existing processes
print_colored "blue" "Cleaning up any existing processes..."
pkill -f "python3.*sensor|python3.*bridge|python3.*llm|python3.*memory" 2>/dev/null || true
sleep 2

# Remove any old pid files
rm -f pids/*.pid 2>/dev/null || true

# Start the bridge server
print_colored "blue" "Starting bridge server..."
start_service "bridge server" "python3 fixed_bridge_server_enhanced.py" "logs/bridge_server.log" "pids/bridge_server.pid"
BRIDGE_SUCCESS=$?

if [ $BRIDGE_SUCCESS -ne 0 ]; then
    print_colored "yellow" "Trying alternative bridge server..."
    start_service "alternative bridge server" "python3 overlay_bridge_server.py" "logs/bridge_server.log" "pids/bridge_server.pid"
    BRIDGE_SUCCESS=$?
    
    if [ $BRIDGE_SUCCESS -ne 0 ]; then
        print_colored "red" "❌ Failed to start bridge server. Exiting..."
        exit 1
    fi
fi

# Wait for bridge to initialize
sleep 3

# Start the LLM service
print_colored "blue" "Starting LLM service..."
start_service "LLM service" "python3 self_contained_llm_ws.py" "logs/llm/self_contained_llm.log" "pids/llm_service.pid"

if [ $? -ne 0 ]; then
    print_colored "red" "❌ Failed to start LLM service. Check logs at logs/llm/self_contained_llm.log"
fi

# Start the memory system
print_colored "blue" "Starting memory system..."
start_service "memory system" "python3 memory/memory_system.py" "logs/memory/memory_system.log" "pids/memory_system.pid"

if [ $? -ne 0 ]; then
    print_colored "red" "❌ Failed to start memory system. Check logs at logs/memory/memory_system.log"
fi

# Start the sensors
print_colored "blue" "Starting sensors..."

# Use the basic screen sensor which is simpler and more reliable
start_service "basic screen sensor" "python3 sensors/basic_screen_sensor.py" "logs/sensors/screen_sensor/screen_sensor.log" "pids/screen_sensor.pid"
if [ $? -ne 0 ]; then
    print_colored "red" "❌ Failed to start screen sensor. Check logs at logs/sensors/screen_sensor/screen_sensor.log"
    print_colored "yellow" "The system will continue without screen sensor, but 'What am I seeing?' queries won't work properly"
fi

# Try enhanced_fixed_process_sensor.py first, and if that fails try regular one
start_service "process sensor" "python3 sensors/enhanced_fixed_process_sensor.py" "logs/sensors/process_sensor/process_sensor.log" "pids/process_sensor.pid"
if [ $? -ne 0 ]; then
    print_colored "yellow" "Trying alternative process sensor..."
    start_service "alternative process sensor" "python3 sensors/process_sensor.py" "logs/sensors/process_sensor/process_sensor.log" "pids/process_sensor.pid"
fi

# Start file sensor
start_service "file sensor" "python3 sensors/file_sensor.py" "logs/sensors/file_sensor/file_sensor.log" "pids/file_sensor.pid"

print_colored "green" "\nCore system is now running with essential components!"
print_colored "blue" "Frontend can connect to ws://localhost:8768 to communicate with the backend"
print_colored "blue" "LLM service is available at ws://localhost:8770"
print_colored "blue" "The system will now collect context from your screen and processes"
print_colored "blue" "When you ask 'What am I seeing?' or 'What application am I using?', the system will use this context to answer"

# Print information about monitoring logs
print_colored "yellow" "\nTo monitor the system:"
echo "tail -f logs/bridge_server.log               # Bridge server logs"
echo "tail -f logs/llm/self_contained_llm.log      # LLM service logs"
echo "tail -f logs/memory/memory_system.log        # Memory system logs"
echo "tail -f logs/sensors/screen_sensor/screen_sensor.log    # Screen sensor logs"
echo "tail -f logs/sensors/process_sensor/process_sensor.log  # Process sensor logs"

# Function to handle shutdown
shutdown() {
    print_colored "yellow" "\nShutting down all services..."
    for pid_file in pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            print_colored "yellow" "Stopping $name (PID: $pid)..."
            kill -9 $pid 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    print_colored "green" "All services stopped."
    exit 0
}

# Set up trap for graceful shutdown
trap shutdown INT TERM

# Print how to stop the system
print_colored "yellow" "\nPress Ctrl+C to stop all services gracefully"
print_colored "yellow" "Or run 'pkill -f \"python3.*sensor|python3.*bridge|python3.*llm|python3.*memory\"' to force stop"

# Keep the script running
while true; do
    sleep 1
done