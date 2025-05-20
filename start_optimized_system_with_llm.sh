#!/bin/bash
# Enhanced optimized system with Enhanced LLM integration (context-aware, sensor and memory integration)
# With minimal logging and periodic log cleanup

# Check if Ollama is installed and running
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install it first:"
    echo "   Visit https://ollama.ai/download for installation instructions"
    exit 1
fi

# Check if Ollama service is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    echo $OLLAMA_PID > pids/ollama.pid
    sleep 5  # Give Ollama time to start
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs/sensors
mkdir -p logs/llm
mkdir -p logs/archive
mkdir -p cache/screen_sensor
mkdir -p memory/screen_data
mkdir -p pids

# Use minimal logging configuration
echo "Setting up minimal logging configuration..."
cp config/logging.conf.minimal config/logging.conf

# Kill any existing processes
echo "Cleaning up any existing processes..."
pkill -f "python3.*\.py" 2>/dev/null || true
sleep 2

# Start the bridge server (critical component for message routing)
echo "Starting fixed bridge server for message routing..."
python3 fixed_bridge_server.py > logs/bridge_server.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
echo "Bridge server started with PID: $BRIDGE_PID"

# Wait for bridge to initialize
sleep 3

# Verify bridge server is running
if ! ps -p $BRIDGE_PID > /dev/null; then
    echo "❌ Bridge server failed to start"
    exit 1
fi

# Start our fixed screen sensor
echo "Starting fixed screen sensor..."
python3 fixed_screen_sensor.py > logs/sensors/screen_sensor.log 2>&1 &
SCREEN_SENSOR_PID=$!
echo $SCREEN_SENSOR_PID > pids/screen_sensor.pid
echo "Screen sensor started with PID: $SCREEN_SENSOR_PID"

# Start the self-contained LLM service
echo "Starting self-contained LLM service..."
python3 self_contained_llm_ws.py > logs/llm/self_contained_llm.log 2>&1 &
LLM_SERVICE_PID=$!
echo $LLM_SERVICE_PID > pids/llm_service.pid
echo "Self-contained LLM service started with PID: $LLM_SERVICE_PID"

# Wait for LLM service to initialize
sleep 3

# Set up periodic log cleanup (every 10 seconds)
echo "Setting up automated log cleanup..."
(while true; do 
    python3 scripts/log_cleanup.py --log-dir logs --max-size 5 --max-age 1 --clear-empty
    sleep 10
done) > logs/log_cleanup.log 2>&1 &
CLEANUP_PID=$!
echo $CLEANUP_PID > pids/log_cleanup.pid
echo "Log cleanup process started with PID: $CLEANUP_PID"

# Now start the enhanced backend server
echo "Starting enhanced backend server..."
./start_enhanced_backend.sh

echo -e "\n\033[0;32mComplete system is now running with all components initialized!\033[0m"
echo -e "\033[0;34mFrontend can connect to ws://localhost:8765 to communicate with the backend\033[0m"
echo -e "\033[0;34mBridge server is available at ws://localhost:8767\033[0m"
echo -e "\033[0;34mLLM service is available at ws://localhost:8766\033[0m"
echo -e "\033[0;34mBackend will manage requests and use Self-contained LLM for context-aware responses\033[0m"
echo -e "\033[0;34mMemory system will provide context for more relevant responses\033[0m"
echo -e "\033[0;34mLog monitor is running in background to manage log file sizes\033[0m"

# Print information about monitoring logs
echo -e "\n\033[0;33mTo monitor the system:\033[0m"
echo "tail -f logs/backend_server.log    # Backend server logs"
echo "tail -f logs/sensors/*.log         # Sensor logs"
echo "tail -f logs/llm/self_contained_llm.log # LLM service logs"
echo "tail -f logs/memory/*.log          # Memory system logs"
echo "tail -f logs/log_monitor.log       # Log monitor status"
echo "tail -f logs/bridge_server.log     # Bridge server logs"

# Function to handle shutdown
shutdown() {
    echo -e "\n\033[0;33mShutting down all services...\033[0m"
    for pid_file in pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid)
            echo "Stopping $name (PID: $pid)..."
            kill -9 $pid 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    # Run final log cleanup before exiting
    echo "Running final log cleanup..."
    python3 scripts/log_cleanup.py --log-dir logs --max-size 5 --max-age 1 --clear-empty
    
    echo -e "\033[0;32mAll services stopped.\033[0m"
    exit 0
}

# Set up trap for graceful shutdown
trap shutdown INT TERM

# Keep the script running
while true; do
    sleep 1
done