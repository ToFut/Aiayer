#!/bin/bash

# Stop the enhanced chat system components
echo "Stopping enhanced chat system with Ollama LLM integration..."

# Function to stop a process by PID file
stop_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null; then
            echo "Stopping $process_name (PID: $PID)..."
            kill $PID
            sleep 1
            if ps -p $PID > /dev/null; then
                echo "Force stopping $process_name..."
                kill -9 $PID
            fi
        else
            echo "$process_name is not running."
        fi
        rm "$pid_file"
    else
        echo "$process_name PID file not found."
    fi
}

# Stop HTTP server
stop_process "pids/http_server.pid" "HTTP Server"

# Stop Ollama service
stop_process "pids/ollama_service.pid" "Ollama LLM Service"

# Stop bridge server
stop_process "pids/bridge_server.pid" "Bridge Server"

echo "All enhanced chat system components have been stopped."