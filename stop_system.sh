#!/bin/bash

# Stop all components of Local AI Assistant

# Function to check if tmux session exists
check_session() {
    tmux has-session -t local_assistant 2>/dev/null
}

# Function to send shutdown signal to a specific pane
shutdown_pane() {
    tmux send-keys -t local_assistant:0.$1 C-c
    sleep 2  # Wait for graceful shutdown
}

# Check if running PIDs file exists
if [ -f .running_pids ]; then
    echo "Stopping Local AI Assistant processes..."
    
    # Kill Python main process
    while read pid; do
        if ps -p $pid > /dev/null; then
            echo "Stopping process $pid..."
            kill $pid
        fi
    done < .running_pids
    
    # Try to find Tauri overlay process
    TAURI_PID=$(ps -ef | grep "[t]auri" | awk '{print $2}')
    if [ ! -z "$TAURI_PID" ]; then
        echo "Stopping Tauri overlay process $TAURI_PID..."
        kill $TAURI_PID
    fi
    
    # Clean up running PIDs file
    rm .running_pids
    echo "Local AI Assistant stopped."
    
# Check if tmux session exists
elif check_session; then
    echo "Shutting down components in tmux session..."
    
    # Send shutdown signals to all components
    shutdown_pane 0  # AI Sensor
    shutdown_pane 1  # File Sensor
    shutdown_pane 2  # Process Sensor
    shutdown_pane 3  # LLM Model
    shutdown_pane 4  # Main Application
    
    # Wait for components to shutdown
    sleep 5
    
    # Kill the tmux session
    tmux kill-session -t local_assistant
    echo "All components stopped successfully"
else
    echo "No running processes found."
    
    # Try to find and kill any stray processes
    echo "Looking for stray processes..."
    PYTHON_PIDS=$(ps -ef | grep "[p]ython3.*main.py" | awk '{print $2}')
    if [ ! -z "$PYTHON_PIDS" ]; then
        echo "Found stray Python processes. Stopping them..."
        for pid in $PYTHON_PIDS; do
            echo "Stopping process $pid..."
            kill $pid
        done
    fi
    
    # Try to find Tauri overlay process
    TAURI_PID=$(ps -ef | grep "[t]auri" | awk '{print $2}')
    if [ ! -z "$TAURI_PID" ]; then
        echo "Stopping Tauri overlay process $TAURI_PID..."
        kill $TAURI_PID
    fi
fi