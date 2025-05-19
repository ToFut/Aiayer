#!/bin/bash
# stop_system.sh
# Script to stop all running Aiayer services

echo "====================================="
echo "    Stopping Aiayer System          "
echo "====================================="

# Define kill functions for different components
kill_by_pid_file() {
  service_name=$1
  pid_file="pids/${service_name}.pid"
  
  if [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    if ps -p $pid > /dev/null; then
      echo "Stopping $service_name (PID: $pid)..."
      kill $pid 2>/dev/null
      sleep 1
      # Force kill if still running
      if ps -p $pid > /dev/null; then
        echo "Force killing $service_name..."
        kill -9 $pid 2>/dev/null
      fi
      echo "✅ $service_name stopped"
    else
      echo "⚠️ $service_name (PID: $pid) not running"
    fi
    # Remove PID file
    rm -f "$pid_file"
  else
    echo "⚠️ No PID file found for $service_name"
  fi
}

kill_by_pattern() {
  pattern=$1
  name=$2
  
  pids=$(ps aux | grep -i "$pattern" | grep -v grep | awk '{print $2}')
  if [ -n "$pids" ]; then
    echo "Stopping $name processes (PIDs: $pids)..."
    for pid in $pids; do
      kill $pid 2>/dev/null
    done
    
    # Wait a second and check if processes are still running
    sleep 1
    still_running=$(ps aux | grep -i "$pattern" | grep -v grep | awk '{print $2}')
    if [ -n "$still_running" ]; then
      echo "Force killing remaining $name processes..."
      for pid in $still_running; do
        kill -9 $pid 2>/dev/null
      done
    fi
    
    echo "✅ $name processes stopped"
  else
    echo "⚠️ No $name processes found running"
  fi
}

# Step 1: Stop all services with PID files
echo "Step 1: Stopping services with PID files..."
for pid_file in pids/*.pid; do
  if [ -f "$pid_file" ]; then
    service_name=$(basename "$pid_file" .pid)
    kill_by_pid_file "$service_name"
  fi
done

# Step 2: Stop any remaining services by pattern
echo "Step 2: Stopping any remaining services by pattern..."
kill_by_pattern "python.*fixed_bridge_server\.py" "bridge server"
kill_by_pattern "python.*ollama_service_fixed\.py" "Enhanced LLM service"
kill_by_pattern "python.*process_sensor\.py" "process sensor"
kill_by_pattern "python.*simple_memory_service\.py" "memory service"
kill_by_pattern "python.*memory_system\.py" "memory system"
kill_by_pattern "npm run tauri" "Tauri overlay"

# Step 3: Clean up any temporary files
echo "Step 3: Cleaning up temporary files..."
# (Add any necessary cleanup here if needed)

# Final check if any processes are still running
echo "Checking for any remaining processes..."
bridge_procs=$(ps aux | grep -i "fixed_bridge_server\.py" | grep -v grep)
llm_procs=$(ps aux | grep -i "ollama_service_fixed\.py" | grep -v grep)
sensor_procs=$(ps aux | grep -i "process_sensor\.py" | grep -v grep)
memory_procs=$(ps aux | grep -i "simple_memory_service\.py\|memory_system\.py" | grep -v grep)
tauri_procs=$(ps aux | grep -i "npm run tauri" | grep -v grep)

if [ -n "$bridge_procs" ] || [ -n "$llm_procs" ] || [ -n "$sensor_procs" ] || [ -n "$memory_procs" ] || [ -n "$tauri_procs" ]; then
  echo "⚠️ Some processes are still running:"
  [ -n "$bridge_procs" ] && echo "Bridge server processes: $(echo "$bridge_procs" | awk '{print $2}')"
  [ -n "$llm_procs" ] && echo "LLM service processes: $(echo "$llm_procs" | awk '{print $2}')"
  [ -n "$sensor_procs" ] && echo "Process sensor processes: $(echo "$sensor_procs" | awk '{print $2}')"
  [ -n "$memory_procs" ] && echo "Memory system processes: $(echo "$memory_procs" | awk '{print $2}')"
  [ -n "$tauri_procs" ] && echo "Tauri overlay processes: $(echo "$tauri_procs" | awk '{print $2}')"
  
  echo "You may need to stop these processes manually."
else
  echo "✅ All Aiayer system processes have been stopped successfully."
fi

echo "====================================="
echo "    Aiayer System Stopped           "
echo "====================================="