#!/bin/bash
#
# Stop Integrated Memory and LLM System
# This script stops all components of the enhanced context-aware LLM system
#

echo "Stopping Integrated Memory and LLM System..."

# Function to gracefully stop a process
stop_process() {
    local pid_file=$1
    local name=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "Stopping $name (PID: $pid)..."
            kill -15 $pid
            
            # Wait for the process to terminate
            count=0
            while ps -p $pid > /dev/null && [ $count -lt 5 ]; do
                echo "Waiting for $name to terminate..."
                sleep 1
                count=$((count+1))
            done
            
            # Force kill if it didn't terminate
            if ps -p $pid > /dev/null; then
                echo "$name did not terminate gracefully, force killing..."
                kill -9 $pid
            else
                echo "$name terminated successfully"
            fi
        else
            echo "$name was not running (PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        echo "No PID file found for $name"
    fi
}

# Stop all components
stop_process "pids/screen_sensor.pid" "Screen Sensor"
stop_process "pids/process_sensor.pid" "Process Sensor"
stop_process "pids/enhanced_ollama_service.pid" "Enhanced Ollama Service"
stop_process "pids/context_memory_server.pid" "Context Memory Server"
stop_process "pids/bridge_server.pid" "Bridge Server"

echo "All components stopped successfully"