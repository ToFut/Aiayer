#!/bin/bash
# Comprehensive system startup script with all latest components
# Includes enhanced sensors, visual processing, app detection, and memory integration

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
    echo $OLLAMA_PID > pids/ollama.pid
    sleep 5  # Give Ollama time to start
fi

# Install required Ollama models
print_colored "blue" "Installing required Ollama models..."
ollama pull llava
ollama pull mistral

# Create necessary directories
print_colored "blue" "Creating necessary directories..."
ensure_dir "logs/sensors/screen_sensor"
ensure_dir "logs/sensors/process_sensor"
ensure_dir "logs/sensors/file_sensor"
ensure_dir "logs/llm"
ensure_dir "logs/memory"
ensure_dir "logs/backend"
ensure_dir "logs/visual"
ensure_dir "logs/app_detection"
ensure_dir "pids"
ensure_dir "cache/screen_sensor"
ensure_dir "cache/process_sensor"
ensure_dir "cache/file_sensor"
ensure_dir "cache/visual"
ensure_dir "cache/app_detection"
ensure_dir "results/app_detection"
ensure_dir "memory/context_snapshots"

# Initialize memory system files
print_colored "blue" "Initializing memory system files..."
touch memory/short_term.idx memory/long_term.idx
echo "[]" > memory/short_term_metadata.json
echo "{}" > memory/conversation_history.json
echo "{}" > memory/memory_state.json
echo "{}" > memory/last_context.json

# Use minimal logging configuration
print_colored "blue" "Setting up minimal logging configuration..."
cp config/logging.conf.minimal config/logging.conf

# Kill any existing processes
print_colored "blue" "Cleaning up any existing processes..."
pkill -f "python3.*\.py" 2>/dev/null || true
sleep 2

# Remove any old pid files
rm -f pids/*.pid 2>/dev/null || true

# Start the enhanced bridge server
print_colored "blue" "Starting enhanced bridge server..."
start_service "enhanced bridge server" "python3 fixed_bridge_server_enhanced.py" "logs/bridge_server.log" "pids/bridge_server.pid"
BRIDGE_SUCCESS=$?

if [ $BRIDGE_SUCCESS -ne 0 ]; then
    print_colored "red" "❌ Failed to start bridge server. Exiting..."
    exit 1
fi

# Wait for bridge to initialize
sleep 3

# Start the LLM service
print_colored "blue" "Starting LLM service..."
start_service "LLM service" "python3 self_contained_llm_ws.py" "logs/llm/self_contained_llm.log" "pids/llm_service.pid"

# Start the enhanced backend server
print_colored "blue" "Starting enhanced backend server..."
start_service "enhanced backend server" "python3 enhanced_backend_server.py" "logs/backend/backend_server.log" "pids/backend_server.pid"

# Start the memory system
print_colored "blue" "Starting memory system..."
start_service "memory system" "python3 memory/memory_system.py" "logs/memory/memory_system.log" "pids/memory_system.pid"

# Start the enhanced sensors
print_colored "blue" "Starting enhanced sensors..."
start_service "enhanced screen sensor" "python3 sensors/enhanced_fixed_screen_sensor.py" "logs/sensors/screen_sensor/screen_sensor.log" "pids/screen_sensor.pid"
start_service "enhanced process sensor" "python3 sensors/enhanced_fixed_process_sensor.py" "logs/sensors/process_sensor/process_sensor.log" "pids/process_sensor.pid"
start_service "file sensor" "python3 sensors/file_sensor.py" "logs/sensors/file_sensor/file_sensor.log" "pids/file_sensor.pid"

# Start visual processing
print_colored "blue" "Starting visual processor..."
start_service "visual processor" "python3 llava_visual_processor.py" "logs/visual/visual_processor.log" "pids/visual_processor.pid"

# Start app detection system
print_colored "blue" "Starting app detection system..."
start_service "app detection" "python3 enhanced_app_detection.py" "logs/app_detection/app_detection.log" "pids/app_detection.pid"
start_service "memory integrator" "python3 app_aware_memory_integrator.py" "logs/memory/memory_integrator.log" "pids/memory_integrator.pid"

# Start the LLM suggestion detector
print_colored "blue" "Starting LLM suggestion detector..."
start_service "suggestion detector" "python3 llm_suggestion_detector.py" "logs/llm/suggestion_detector.log" "pids/suggestion_detector.pid"

# Set up periodic log cleanup
print_colored "blue" "Setting up automated log cleanup..."
(while true; do 
    python3 scripts/log_cleanup.py --log-dir logs --max-size 5 --max-age 1 --clear-empty
    sleep 10
done) > logs/log_cleanup.log 2>&1 &
CLEANUP_PID=$!
echo $CLEANUP_PID > pids/log_cleanup.pid

print_colored "green" "\nComplete system is now running with all components initialized!"
print_colored "blue" "Frontend can connect to ws://localhost:8768 to communicate with the backend"
print_colored "blue" "Bridge server is available at ws://localhost:8768"
print_colored "blue" "LLM service is available at ws://localhost:8770"
print_colored "blue" "Backend will manage requests and use Self-contained LLM for context-aware responses"
print_colored "blue" "Memory system will provide context for more relevant responses"
print_colored "blue" "Visual processor and app detection are running for enhanced context awareness"
print_colored "blue" "Log monitor is running in background to manage log file sizes"

# Print information about monitoring logs
print_colored "yellow" "\nTo monitor the system:"
echo "tail -f logs/backend/backend_server.log    # Backend server logs"
echo "tail -f logs/sensors/*/*.log               # Sensor logs"
echo "tail -f logs/llm/*.log                     # LLM service logs"
echo "tail -f logs/memory/*.log                  # Memory system logs"
echo "tail -f logs/visual/*.log                  # Visual processor logs"
echo "tail -f logs/app_detection/*.log           # App detection logs"
echo "tail -f logs/bridge_server.log             # Bridge server logs"

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
    
    # Run final log cleanup before exiting
    print_colored "yellow" "Running final log cleanup..."
    python3 scripts/log_cleanup.py --log-dir logs --max-size 5 --max-age 1 --clear-empty
    
    print_colored "green" "All services stopped."
    exit 0
}

# Set up trap for graceful shutdown
trap shutdown INT TERM

# Keep the script running
while true; do
    sleep 1
done 