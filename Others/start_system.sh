#!/bin/bash

# Create necessary directories
mkdir -p logs/memory logs/llm logs/sensors pids

# Function to check if a process is running
check_process() {
    if [ -f "pids/$1.pid" ]; then
        pid=$(cat "pids/$1.pid")
        if ps -p $pid > /dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to start a service
start_service() {
    local service=$1
    local script=$2
    local log_file="logs/${service}.log"
    
    echo "Starting $service..."
    python3 $script > $log_file 2>&1 &
    echo $! > "pids/$service.pid"
    sleep 2
    
    if check_process $service; then
        echo "✅ $service started successfully"
    else
        echo "❌ Failed to start $service"
        exit 1
    fi
}

# Kill any existing processes
echo "Cleaning up existing processes..."
for service in bridge_server memory_service llm_service; do
    if check_process $service; then
        pid=$(cat "pids/$service.pid")
        kill $pid 2>/dev/null
        rm "pids/$service.pid"
    fi
done

# Start services in order
echo "Starting services..."

# 1. Start bridge server
start_service "bridge_server" "bridge_server.py"

# 2. Start memory service
start_service "memory_service" "memory/memory_service.py"

# 3. Start LLM service
start_service "llm_service" "llm/llm_service.py"

echo "All services started successfully"
echo "System is ready"

# Keep script running and handle cleanup on exit
trap 'echo "Stopping services..."; for service in bridge_server memory_service llm_service; do if check_process $service; then pid=$(cat "pids/$service.pid"); kill $pid 2>/dev/null; rm "pids/$service.pid"; fi; done' EXIT

# Wait for user interrupt
echo "Press Ctrl+C to stop all services"
while true; do
    sleep 1
done 