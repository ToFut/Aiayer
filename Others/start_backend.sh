#!/bin/bash
# start_backend.sh
# Consolidated script that starts all backend components including the fixed WebSocket bridge
#
# Required Python dependencies:
# pip install aiohttp pillow websockets

set -e
echo "=== Starting Aiayer Backend System ==="

# Check and install required Python dependencies
echo "Checking required Python dependencies..."
pip install -q aiohttp pillow websockets || {
  echo "⚠️ Failed to install dependencies. Attempting to continue anyway...";
}

# Create required directories
mkdir -p logs/sensors
mkdir -p logs/memory
mkdir -p logs/llm
mkdir -p pids
mkdir -p cache/process_sensor
mkdir -p cache/screen_sensor
mkdir -p cache/file_sensor
mkdir -p memory

# Function to kill processes
kill_process() {
  process_name=$1
  echo "Stopping ${process_name} processes..."
  pids=$(ps aux | grep -i ${process_name} | grep -v grep | awk '{print $2}')
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

# Step 1: Stop any running processes
echo "Step 1: Stopping any running processes..."
kill_process "bridge_server"
kill_process "process_sensor"
kill_process "memory_system"
kill_process "llm_service"
echo "All processes stopped"

# Step 2: Initialize cache files
echo "Step 2: Initializing cache files..."

# Initialize process cache
echo '{
  "timestamp": '$(date +%s)',
  "processes": []
}' > "cache/process_sensor/process_cache.json"

# Initialize screen cache
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

# Initialize last_context.json
echo '{
  "timestamp": '$(date +%s)',
  "active_window": "",
  "active_app": "",
  "active_apps": [],
  "window_history": [],
  "screen_text": ""
}' > "memory/last_context.json"

echo "Cache files initialized"

# Step 3: Start the fixed bridge server (using the most robust implementation)
echo "Step 3: Starting fixed bridge server..."
# First check if there's already a bridge server running
if ps aux | grep -v grep | grep -q "fixed_bridge_server_new.py"; then
  echo "Bridge server already running. Stopping it first..."
  pkill -f "python.*fixed_bridge_server_new.py" || true
  sleep 2
fi

# Start the bridge server
python3 fixed_bridge_server_new.py > logs/fixed_bridge.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
echo "Bridge server started with PID $BRIDGE_PID"

# Wait for bridge server to initialize and verify it's running
sleep 3
if ps -p $BRIDGE_PID > /dev/null; then
  echo "✅ Bridge server started successfully"
else
  echo "❌ Bridge server failed to start. Check logs/fixed_bridge.log for details"
  cat logs/fixed_bridge.log | tail -n 20
  exit 1
fi

# Step 4: Start the process sensor
echo "Step 4: Starting process sensor..."
python3 sensors/process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
PROCESS_SENSOR_PID=$!
echo $PROCESS_SENSOR_PID > pids/process_sensor.pid
echo "Process sensor started with PID $PROCESS_SENSOR_PID"

# Step 5: Start the memory system (using simple standalone version)
echo "Step 5: Starting memory system..."
python3 simple_memory_service.py > logs/memory/memory_service.log 2>&1 &
MEMORY_PID=$!
echo $MEMORY_PID > pids/memory_service.pid
echo "Memory service started with PID $MEMORY_PID"

# Step 6: Start the Enhanced LLM service
echo "Step 6: Starting Enhanced LLM service with context, memory and sensor integration..."
# Check if there's already an LLM service running
if ps aux | grep -v grep | grep -q "ollama_service_fixed.py"; then
  echo "Enhanced LLM service already running. Stopping it first..."
  pkill -f "python.*ollama_service_fixed.py" || true
  sleep 2
fi

# Start the Enhanced LLM service
python3 ollama_service_fixed.py > logs/llm/ollama_service.log 2>&1 &
LLM_PID=$!
echo $LLM_PID > pids/ollama_service.pid
echo "Enhanced LLM service started with PID $LLM_PID"

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 3

# Verify services are running
echo "Verifying services..."
all_services_running=true

# Service list to check (excluding bridge_server since we already verified it)
services=("process_sensor" "memory_service" "llm_service")

for service in "${services[@]}"; do
    pid_file="pids/${service}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "✅ Service ${service} is running (PID: $pid)"
        else
            echo "❌ Service ${service} failed to start"
            log_file=""
            case $service in
                process_sensor)
                    log_file="logs/sensors/process_sensor.log"
                    ;;
                memory_service)
                    log_file="logs/memory/memory_service.log"
                    ;;
                llm_service)
                    log_file="logs/llm/llm_service.log"
                    ;;
            esac
            
            if [ -n "$log_file" ] && [ -f "$log_file" ]; then
                echo "Last 10 lines of $log_file:"
                tail -n 10 "$log_file"
            fi
            
            all_services_running=false
        fi
    else
        echo "⚠️  No PID file found for service ${service}"
    fi
done

if [ "$all_services_running" = false ]; then
    echo "❌ One or more services failed to start. Please check the logs for details."
    exit 1
fi

echo "=== Backend System Started Successfully ==="
echo "Bridge server PID: $BRIDGE_PID"
echo "Process sensor PID: $PROCESS_SENSOR_PID"
echo "Memory service PID: $MEMORY_PID"
echo "LLM service PID: $LLM_PID"
echo ""
echo "To check logs:"
echo "tail -f logs/fixed_bridge.log    # Bridge server logs"
echo "tail -f logs/sensors/process_sensor.log  # Process sensor logs"
echo "tail -f logs/memory/memory_service.log    # Memory service logs"
echo "tail -f logs/llm/llm_service.log        # LLM service logs"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid)"