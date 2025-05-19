#!/bin/bash

# Start Memory Search System
# This script starts the complete system with enhanced semantic search capabilities

echo "===== Starting Semantic Search Enhanced System ====="
echo "This script will start all required components for semantic search"

# Create necessary directories
mkdir -p logs pids cache

# Function to check if a port is in use
check_port() {
  if lsof -i:$1 > /dev/null 2>&1; then
    return 0 # Port is in use
  else
    return 1 # Port is not in use
  fi
}

# Function to kill a process by PID file
kill_pid() {
  if [ -f "$1" ]; then
    pid=$(cat "$1")
    if ps -p $pid > /dev/null 2>&1; then
      echo "Killing existing process (PID: $pid)..."
      kill -9 $pid
    fi
    rm "$1"
  fi
}

# Kill any existing processes
echo "Checking for existing processes..."
kill_pid "pids/memory_system.pid"
kill_pid "pids/memory_bridge.pid"
kill_pid "pids/ws_server_8765.pid"

# Check if ports are still in use
for port in 8765 8766; do
  if check_port $port; then
    echo "Port $port is still in use! Please free this port and try again."
    echo "You can use 'lsof -i:$port' to find the process."
    exit 1
  fi
}

# Start memory system
echo "Starting memory system..."
python memory/memory_system.py > logs/memory_system.log 2>&1 &
echo $! > pids/memory_system.pid
sleep 2

# Start WebSocket server on port 8765
echo "Starting WebSocket server on port 8765..."
python ws_server_8765.py > logs/ws_server_8765.log 2>&1 &
echo $! > pids/ws_server_8765.pid
sleep 2

# Start memory bridge with semantic search
echo "Starting memory bridge with semantic search..."
python final_memory_bridge.py > logs/memory_bridge.log 2>&1 &
echo $! > pids/memory_bridge.pid
sleep 2

echo "System started! Components running:"
echo "1. Memory System (PID: $(cat pids/memory_system.pid))"
echo "2. WebSocket Server on port 8765 (PID: $(cat pids/ws_server_8765.pid))"
echo "3. Memory Bridge with Semantic Search (PID: $(cat pids/memory_bridge.pid))"
echo ""
echo "The overlay should connect to ws://localhost:8766"
echo "You can test semantic search by asking questions like:"
echo "  - 'search for recent messages'"
echo "  - 'find information about X'"
echo "  - 'what do you remember about Y'"
echo ""
echo "To stop the system, run: ./stop_system.sh"
echo "To view logs: tail -f logs/memory_bridge.log"
echo "====================================================="