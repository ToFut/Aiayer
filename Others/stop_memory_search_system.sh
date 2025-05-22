#!/bin/bash

# Stop Memory Search System
# This script stops all components started by start_memory_search_system.sh

echo "===== Stopping Semantic Search Enhanced System ====="

# Function to kill a process by PID file
kill_pid() {
  if [ -f "$1" ]; then
    pid=$(cat "$1")
    if ps -p $pid > /dev/null 2>&1; then
      echo "Stopping $2 (PID: $pid)..."
      kill $pid
      sleep 1
      # If process is still running, force kill
      if ps -p $pid > /dev/null 2>&1; then
        echo "Process not responding, force killing..."
        kill -9 $pid
      fi
    else
      echo "$2 is not running (PID: $pid)"
    fi
    rm "$1"
  else
    echo "No PID file found for $2"
  fi
}

# Stop all components
kill_pid "pids/memory_bridge.pid" "Memory Bridge"
kill_pid "pids/ws_server_8765.pid" "WebSocket Server"
kill_pid "pids/memory_system.pid" "Memory System"

echo "All components stopped successfully."
echo "====================================================="