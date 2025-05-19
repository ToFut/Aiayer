#!/bin/bash
# start_fixed_complete_system.sh
# A comprehensive script that starts the fixed system with all components

set -e
echo "=== Starting Fixed Complete System ==="

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

# Step 3: Start the bridge server
echo "Step 3: Starting bridge server..."
python3 start_bridge_server.py > logs/bridge_server.log 2>&1 &
BRIDGE_PID=$!
echo $BRIDGE_PID > pids/bridge_server.pid
echo "Bridge server started with PID $BRIDGE_PID"

# Wait for bridge server to initialize
sleep 2

# Step 4: Start the process sensor
echo "Step 4: Starting process sensor..."
python3 sensors/process_sensor.py > logs/sensors/process_sensor.log 2>&1 &
PROCESS_SENSOR_PID=$!
echo $PROCESS_SENSOR_PID > pids/process_sensor.pid
echo "Process sensor started with PID $PROCESS_SENSOR_PID"

# Step 5: Start the memory system
echo "Step 5: Starting memory system..."
python3 memory/memory_system.py > logs/memory/memory_system.log 2>&1 &
MEMORY_PID=$!
echo $MEMORY_PID > pids/memory_system.pid
echo "Memory system started with PID $MEMORY_PID"

# Step 6: Start the LLM service
echo "Step 6: Starting LLM service..."
python3 llm/llm_service.py > logs/llm/llm_service.log 2>&1 &
LLM_PID=$!
echo $LLM_PID > pids/llm_service.pid
echo "LLM service started with PID $LLM_PID"

# Step 7: Start the Tauri overlay
echo "Step 7: Starting Tauri overlay..."
cd overlay && npm run tauri dev &
TAURI_PID=$!
echo $TAURI_PID > pids/tauri.pid
echo "Tauri overlay started with PID $TAURI_PID"

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 3

# Verify services are running
echo "Verifying services..."
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "✅ Service $(basename "$pid_file" .pid) is running (PID: $pid)"
        else
            echo "❌ Service $(basename "$pid_file" .pid) failed to start"
            exit 1
        fi
    fi
done

echo "=== Fixed Complete System Started Successfully ==="
echo "Bridge server PID: $BRIDGE_PID"
echo "Process sensor PID: $PROCESS_SENSOR_PID"
echo "Memory system PID: $MEMORY_PID"
echo "LLM service PID: $LLM_PID"
echo "Tauri overlay PID: $TAURI_PID"
echo ""
echo "To check logs:"
echo "tail -f logs/bridge_server.log    # Bridge server logs"
echo "tail -f logs/sensors/process_sensor.log  # Process sensor logs"
echo "tail -f logs/memory/memory_system.log    # Memory system logs"
echo "tail -f logs/llm/llm_service.log        # LLM service logs"
echo ""
echo "To stop all services:"
echo "kill \$(cat pids/*.pid)"