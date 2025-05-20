#!/bin/bash
# Script to stop the running memory system

# Set working directory to the script location
cd "$(dirname "$0")"

echo "Stopping Conscious Memory System"
echo "================================"

# Find and stop the memory update process
RUNNER_PID=$(ps aux | grep "python3 run_memory_update.py" | grep -v grep | awk '{print $2}')

if [ -z "$RUNNER_PID" ]; then
    echo "No running memory system processes found."
else
    echo "Found memory system process with PID: $RUNNER_PID"
    echo "Sending terminate signal..."
    kill -TERM $RUNNER_PID
    
    # Wait for process to terminate
    sleep 2
    
    # Check if process is still running
    if ps -p $RUNNER_PID > /dev/null; then
        echo "Process still running, force killing..."
        kill -9 $RUNNER_PID
        
        # Verify process was killed
        if ! ps -p $RUNNER_PID > /dev/null; then
            echo "Process successfully terminated."
        else
            echo "Failed to kill process. Please terminate manually."
        fi
    else
        echo "Process successfully terminated."
    fi
fi

echo "================================"
echo "Memory system stopped"