#!/bin/bash

# Function to check if tmux session exists
check_session() {
    tmux has-session -t local_assistant 2>/dev/null
}

# Function to send shutdown signal to a specific pane
shutdown_pane() {
    tmux send-keys -t local_assistant:0.$1 C-c
    sleep 2  # Wait for graceful shutdown
}

# Check if session exists
if check_session; then
    echo "Shutting down components..."
    
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
    echo "No running session found"
fi 